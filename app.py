import numpy as np
import datetime as dt
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect, distinct, desc

from flask import Flask, jsonify

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an the database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to both tables
Measurement = Base.classes.measurement
Station = Base.classes.station

session = Session(engine)

# Calculate the date an year ago from the last data point in the database
last_date = session.query(Measurement.date).\
    order_by(Measurement.date.desc()).first()
year_ago = dt.datetime.strptime(last_date[0], '%Y-%m-%d')\
    .date() - dt.timedelta(days=365)

# Calculate the first data point in the database
first_date = session.query(Measurement.date).\
    order_by(Measurement.date.asc()).first()

# Save the list of all dates
date_list = np.ravel(session.query(Measurement.date).all())

session.close()

# Flask Setup
app = Flask(__name__)

# Flask Routes


@app.route("/")
def homepage():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/2016-10-09<br/>"
        f"/api/v1.0/2016-10-09/2016-10-30"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    """Return the last 12 months of precipitation data"""
    # Perform a query to retrieve the data and precipitation scores
    prcps = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= year_ago).\
        order_by(Measurement.date).all()

    session.close()

    # Convert the query results to a dictionary using (date: prcp) as the key, value pairs
    all_prcps = []
    for date, prcp in prcps:
        prcp_dict = {}
        prcp_dict[date] = prcp

        all_prcps.append(prcp_dict)

    return jsonify(all_prcps)


@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for 'Stations' page ...")
    session = Session(engine)
    stations = session.query(Station.name)
    session.close()

    station_list = []
    for row in stations:
        station_list.append(row[0])

    return jsonify(station_list)


@app.route("/api/v1.0/tobs")
def last_year():
    session = Session(engine)
    station_count = session.query(Measurement.station.distinct(), func.count('*')).\
        group_by(Measurement.station).order_by(func.count('*').desc())

    filter = session.query(Measurement.date, Measurement.station, Measurement.tobs).\
        filter(Measurement.station == station_count.first()[0]).\
        filter(Measurement.date >= '2016-08-23').\
        order_by(Measurement.date).all()
    session.close()

    filter_df = pd.DataFrame(
        filter, columns=['Date', 'Station', 'tobs'])
    observations = filter_df['tobs'].tolist()
    return jsonify(observations)


@app.route("/api/v1.0/<start>")
def temp_stats(start):
    session = Session(engine)
    temp_max = session.query(func.max(Measurement.tobs)).filter(
        Measurement.date >= start)
    temp_min = session.query(func.min(Measurement.tobs)).filter(
        Measurement.date >= start)
    temp_avg = session.query(func.avg(Measurement.tobs)).filter(
        Measurement.date >= start)
    session.close()

    temp_list = [temp_min[0][0], round(temp_avg[0][0], 2), temp_max[0][0]]
    return jsonify(temp_list)


@app.route("/api/v1.0/<start>/<end>")
def temp_stats_range(start, end):
    session = Session(engine)
    temp_max = session.query(func.max(Measurement.tobs)).filter(
        Measurement.date >= start).filter(Measurement.date <= end)
    temp_min = session.query(func.min(Measurement.tobs)).filter(
        Measurement.date >= start).filter(Measurement.date <= end)
    temp_avg = session.query(func.avg(Measurement.tobs)).filter(
        Measurement.date >= start).filter(Measurement.date <= end)
    session.close()

    temp_list = [temp_min[0][0], round(temp_avg[0][0], 2), temp_max[0][0]]
    return jsonify(temp_list)


if __name__ == '__main__':
    app.run(debug=True)
