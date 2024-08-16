from flask import Flask, request, jsonify
from shapely.geometry import Point, Polygon
import geopandas as gpd
import matplotlib.pyplot as plt
import math
from io import BytesIO
import base64
from flask_cors import CORS  # Import CORS


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins (for development)
# Function to parse deed calls
def parse_deed_calls(deed_calls):
    directions = []
    distances = []

    call_lines = deed_calls.strip().splitlines()

    for line in call_lines:
        parts = line.split()
        direction = parts[0].strip().upper()  # Ensure consistent case
        distance = float(parts[1].strip('f'))  # Assuming 'f' for feet
        directions.append(direction)
        distances.append(distance)

    return directions, distances

# Function to calculate the next point based on the current point, bearing, and distance
def calculate_point(start_point, direction, distance):
    # Extract the angle by removing the first and last characters (which are N, S, E, W)
    angle_str = direction[1:-1]
    
    # Convert the angle string to a float
    angle = float(angle_str)

    # Calculate the bearing based on direction
    if direction.startswith('N'):
        if direction.endswith('E'):
            bearing = angle
        else:  # direction ends with 'W'
            bearing = 360 - angle
    elif direction.startswith('S'):
        if direction.endswith('E'):
            bearing = 180 - angle
        else:  # direction ends with 'W'
            bearing = 180 + angle
    
    # Convert bearing to radians
    bearing_rad = math.radians(bearing)
    
    # Calculate the change in x and y with high precision
    dx = distance * math.sin(bearing_rad)
    dy = distance * math.cos(bearing_rad)
    
    # Return the new point
    return Point(round(start_point.x + dx, 10), round(start_point.y + dy, 10))

@app.route('/plot', methods=['POST'])
def plot_deed():
    data = request.json
    deed_calls = data.get('deed_calls', '')

    # Parse the deed calls
    directions, distances = parse_deed_calls(deed_calls)

    # Start plotting from origin
    points = [Point(0, 0)]

    # Calculate each subsequent point
    for direction, distance in zip(directions, distances):
        new_point = calculate_point(points[-1], direction, distance)
        points.append(new_point)

    # Create a Polygon from the points
    polygon = Polygon(points)

    # Plotting with Geopandas
    gdf = gpd.GeoDataFrame(geometry=[polygon])
    gdf.plot(color='yellow', edgecolor='black', linewidth=2)

    # Annotate the plot with labels for each segment
    for i, (direction, distance) in enumerate(zip(directions, distances)):
        plt.text(points[i].x, points[i].y, f'{direction} {distance}f', fontsize=8, color='red')

    # Save the plot to a BytesIO object
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    plt.close()
    img_buf.seek(0)

    # Encode the image in base64
    img_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')

    # Return the image in base64 format
    return jsonify({'image': img_base64})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
