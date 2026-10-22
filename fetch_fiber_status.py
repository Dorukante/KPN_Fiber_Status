
import pandas as pd
import time
import re
from pathlib import Path
from playwright.sync_api import sync_playwright


class Fiber:
    """Retrieve and classify KPN fiber availability for Dutch addresses."""

    def __init__(self):
        """Set the KPN fiber availability website."""
        self.url = "https://www.kpn.com/glasvezelnetwerk"

    def extract_status(self, text):
        """
        Classify the KPN response using predefined Dutch phrases.

        Args:
            text (str): KPN response message.

        Returns:
            str: Active, Planned, Currently Installing,
                 Not Available, or Unknown.
        """
        text = text.lower()

        if (
            "jouw woning heeft glasvezel van kpn" in text
            or "jouw nieuwbouwwoning heeft glasvezel" in text
            or "op jouw adres is glasvezel beschikbaar" in text
        ):
            return "Active"

        elif (
            "we maken plannen voor de aanleg van glasvezel" in text
            or "jouw woning krijgt glasvezel" in text
            or "jouw nieuwbouwwoning krijgt glasvezel" in text
            or "nog even geduld" in text
            or "we sluiten je woning" in text
        ):
            return "Planned"

        elif (
            "geen glasvezel beschikbaar" in text
            or "we hebben je woning niet kunnen aansluiten" in text
            or "op dit moment is het niet mogelijk een (extra) glasvezelaansluiting te maken op dit adres" in text
        ):
            return "Not Available"

        elif "legt glasvezel aan in jouw buurt" in text:
            return "Currently Installing"

        return "Unknown"

    def check_address(self, address, kpn_address):
        """
        Check whether the returned KPN address matches the PDOK address.

        Args:
            address (pandas.Series): Original PDOK address.
            kpn_address (str): Address displayed by KPN.

        Returns:
            bool: True if the addresses match after normalization.
        """

        expected = f"{address['street']} {address['house_number']}"

        if address["addition"]:
            expected += f"-{address['addition']}"

        # Remove the city from the KPN address
        kpn_street = re.split(
            r"\s+in\s+",
            kpn_address,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0]

        def normalize(text):
            """Standardize punctuation, abbreviations, and spacing."""
            text = text.lower().strip()
            text = text.replace(".", " ")
            text = re.sub(r"\s*-\s*", " ", text)
            text = re.sub(r"straat\b", "str", text)
            text = re.sub(r"laan\b", "ln", text)
            text = re.sub(r"\s+", " ", text)
            return text

        return normalize(expected) == normalize(kpn_street)

    def retrieve_status(
        self,
        path_adress="Data/addresses.csv",
        path_fiber="Data/fiber_status.csv"
    ):
        """
        Check KPN fiber availability for addresses in a CSV file.

        Args:
            path_adress (str): Input CSV containing PDOK addresses.
            path_fiber (str): Output CSV for fiber availability results.

        Returns:
            pandas.DataFrame: Address data with fiber_status,
                              kpn_address, and error columns.

        Notes:
            Uses one browser and one tab, checks each address once,
            and saves results after each lookup.
        """

        addresses = pd.read_csv(path_adress, dtype=str).fillna("")
        Path(path_fiber).parent.mkdir(parents=True, exist_ok=True)

        results = []

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            try:
                for index, address in addresses.iterrows():

                    postcode = address["postcode"].strip()
                    number = address["house_number"].strip()
                    addition = address["addition"].strip()

                    print(
                        f"Checking {index + 1}/{len(addresses)}: "
                        f"{postcode} {number}-{addition}"
                    )

                    status = "Error"
                    kpn_address = ""
                    error = ""

                    try:
                        # Open KPN using the same browser tab
                        page.goto(
                            self.url,
                            wait_until="domcontentloaded",
                            timeout=30000
                        )

                        # Locate the address form
                        postcode_field = page.locator('input[name="zipCode"]')
                        number_field = page.locator('input[name="houseNumber"]')
                        addition_field = page.locator(
                            'input[name="houseNumberExtension"]'
                        )

                        # Wait for the form to load
                        postcode_field.wait_for(state="visible")
                        page.wait_for_timeout(1500)

                        # Enter address information
                        postcode_field.fill(postcode)
                        postcode_field.press("Tab")
                        page.wait_for_timeout(700)

                        number_field.fill(number)
                        number_field.press("Tab")
                        page.wait_for_timeout(700)

                        addition_field.fill(addition)
                        addition_field.press("Tab")
                        page.wait_for_timeout(700)

                        # Verify required fields were not cleared
                        entered_postcode = postcode_field.input_value()
                        entered_number = number_field.input_value()

                        if (
                            entered_postcode.replace(" ", "").upper()
                            != postcode.replace(" ", "").upper()
                            or entered_number != number
                        ):
                            raise ValueError(
                                "KPN cleared the postcode or house number"
                            )

                        # Submit the address
                        page.get_by_role(
                            "button", name="Check", exact=True
                        ).click()

                        # Wait for the result
                        page.get_by_text(
                            "Jouw adres:", exact=False
                        ).first.wait_for(timeout=25000)

                        page.wait_for_timeout(1000)

                        # Extract the address and availability message
                        text = page.locator("body").inner_text()
                        result_text = text.split("Jouw adres:", 1)[1]

                        lines = [
                            line.strip()
                            for line in result_text.splitlines()
                            if line.strip()
                        ]

                        kpn_address = lines[0] if lines else ""

                        message = result_text.split(
                            "Waarmee kunnen we je helpen?", 1
                        )[0].strip()

                        # Verify the address and classify the status
                        if self.check_address(address, kpn_address):
                            status = self.extract_status(message)
                        else:
                            status = "Address Mismatch"

                    except Exception as e:
                        error = str(e)
                        print(f"Error: {error[:200]}")

                    # Store the result
                    result = address.to_dict()
                    result["fiber_status"] = status
                    result["kpn_address"] = kpn_address
                    result["error"] = error

                    results.append(result)

                    print(f"KPN address: {kpn_address}")
                    print(f"Status: {status}\n")

                    # Save progress after each address
                    pd.DataFrame(results).to_csv(
                        path_fiber, index=False
                    )

                    # Pause between lookups
                    time.sleep(3)

            finally:
                browser.close()

        return pd.DataFrame(results)


if __name__ == "__main__":
    checker = Fiber()
    df = checker.retrieve_status()
