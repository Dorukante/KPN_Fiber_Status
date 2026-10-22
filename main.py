from flask import Flask, render_template, jsonify, send_from_directory, request
import os
import pandas as pd

app = Flask(__name__, template_folder="Template")

@app.route("/", methods=["GET"])
def homePage():
    return render_template("Main.html")

@app.route("/get-<path:filename>")
def getResource(filename):
    return send_from_directory(app.template_folder, filename)

@app.route("/api/fiber-status")
def get_fiber_status():

    # Read CSV file
    path_for_data = os.path.join(os.path.curdir, "Data")
    path_for_fiber = os.path.join(path_for_data, "fiber_status.csv")
    df = pd.read_csv(path_for_fiber).fillna("")

    # Convert DataFrame to JSON
    return jsonify(df.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(debug=False, port=8000)