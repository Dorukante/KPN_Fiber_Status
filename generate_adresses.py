
import requests
import pandas as pd
import random
import os
import re


class Adress:
    """
    Generate random Dutch addresses using the PDOK Locatieserver API.

    The class retrieves address records from nine Dutch cities,
    validates postal codes, removes duplicate addresses, and
    randomly selects up to 10 addresses per city.

    Only the information required for KPN fiber status lookups
    and geographic visualization is retained.
    """

    def __init__(self):
        """
        Initialize the PDOK API endpoint and the selected cities.
        """

        self.url = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"

        self.cities = [
            "Utrecht",
            "Amsterdam",
            "'s-Gravenhage",
            "Eindhoven",
            "Groningen",
            "Rotterdam",
            "Arnhem",
            "Zwolle",
            "Leeuwarden"
        ]

    def retrieve_adress(self):
        """
        Retrieve random addresses from selected Dutch cities.

        For each city, the method:
            1. Requests up to 100 address records from PDOK.
            2. Validates postal codes and required fields.
            3. Removes duplicate physical addresses.
            4. Randomly selects up to 10 unique addresses.
            5. Extracts geographic coordinates.
            6. Saves the results to a CSV file.

        Returns:
            pandas.DataFrame:
                A DataFrame containing seven columns:

                - postcode: Dutch postal code.
                - house_number: House number.
                - addition: Combined house letter and addition.
                - street: Street name.
                - city: City name.
                - latitude: Geographic latitude.
                - longitude: Geographic longitude.

        Saves:
            Data/addresses.csv:
                CSV containing the generated addresses.

        Raises:
            requests.exceptions.RequestException:
                If a PDOK API request fails.

            KeyError:
                If the expected API response structure is missing.

            ValueError:
                If geographic coordinates cannot be converted
                to floating-point values.
        """

        addresses = []

        # Retrieve up to 10 random addresses from each city
        for city in self.cities:

            # Set API parameters to retrieve up to 100 address records
            params = {
                "fq": [
                    "type:adres",
                    f'woonplaatsnaam:"{city}"'
                ],
                "rows": 100
            }

            # Request address records from PDOK
            response = requests.get(
                self.url,
                params=params,
                timeout=15
            )

            response.raise_for_status()

            # Extract returned address records
            data = response.json()["response"]["docs"]

            # Keep only valid addresses
            valid_addresses = [
                address for address in data
                if re.fullmatch(
                    r"[1-9][0-9]{3}[A-Z]{2}",
                    str(address.get("postcode") or "")
                    .replace(" ", "")
                    .upper()
                )
                and address.get("huisnummer") is not None
                and address.get("centroide_ll")
                and address.get("straatnaam")
                and address.get("woonplaatsnaam", "").lower() == city.lower()
            ]

            # Remove duplicate physical addresses
            unique_addresses = {}

            for address in valid_addresses:

                key = (
                    str(address["postcode"]).replace(" ", "").upper(),
                    str(address["huisnummer"]),
                    address.get("huisletter") or "",
                    address.get("huisnummertoevoeging") or ""
                )

                unique_addresses[key] = address

            valid_addresses = list(unique_addresses.values())


            selected = random.sample(
                valid_addresses,
                10
            )

            for address in selected:

                # Extract coordinates (longitude first)
                coordinates = address["centroide_ll"]

                coordinates = coordinates.replace(
                    "POINT(", ""
                ).replace(")", "")

                longitude, latitude = map(
                    float,
                    coordinates.split()
                )

                # Extract house number and optional additions
                house_number = address["huisnummer"]

                house_letter = address.get("huisletter") or ""
                house_addition = address.get("huisnummertoevoeging") or ""

                # Combine additions for KPN lookup
                addition = house_letter + house_addition

                # Store only required address information
                addresses.append({
                    "postcode": str(address["postcode"])
                                .replace(" ", "").upper(),

                    "house_number": house_number,

                    "addition": addition,

                    "street": address["straatnaam"],

                    "city": (
                        "Den Haag"
                        if city == "'s-Gravenhage"
                        else address["woonplaatsnaam"]
                    ),

                    "latitude": latitude,
                    "longitude": longitude
                })

        # Convert addresses into a DataFrame
        df = pd.DataFrame(
            addresses,
            columns=[
                "postcode",
                "house_number",
                "addition",
                "street",
                "city",
                "latitude",
                "longitude"
            ]
        )

        # Create the Data directory if necessary
        os.makedirs("Data", exist_ok=True)

        # Save addresses to CSV
        df.to_csv(
            "Data/addresses.csv",
            index=False
        )

        print(f"\nTotal addresses saved: {len(df)}")

        return df


# Run address generation only when executed directly
if __name__ == "__main__":

    generator = Adress()

    df = generator.retrieve_adress()
