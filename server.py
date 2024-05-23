from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
import mysql.connector
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
import os
from datetime import datetime
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from numpy import mean, concatenate, array, hstack
import codecs, json 
import datetime
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)






#############################################################################################
##################################### Swagger ###############################################
#############################################################################################
SWAGGER_URL = '/swagger'
API_URL = '/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Your API Name"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)






#############################################################################################
##################################### database Connect ######################################
#############################################################################################




TABLE_NAME = 'price_prod'

# Create database and connection
try:
    mydb = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME")
    )
    cursor = mydb.cursor()

    # Create product_detail table if not exists
    create_product_detail_table = """
    CREATE TABLE IF NOT EXISTS product_detail (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE
    )
    """
    cursor.execute(create_product_detail_table)

    # Create price_prod table if not exists
    create_price_prod_table = """
    CREATE TABLE IF NOT EXISTS price_prod (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date_price DATE NOT NULL,
        date_create DATE NOT NULL,
        product_id INT NOT NULL,
        minPrice INT NOT NULL,
        maxPrice INT NOT NULL,
        avgPrice INT NOT NULL,
        unit VARCHAR(255) NOT NULL,
        FOREIGN KEY (product_id) REFERENCES product_detail(id)
    )
    """
    cursor.execute(create_price_prod_table)



    # Define the SQL query
    create_predict = """
    CREATE TABLE IF NOT EXISTS price_predict_melon (
        id INT AUTO_INCREMENT PRIMARY KEY,
        price_pred FLOAT NOT NULL
    )
    """

    # Execute the query
    cursor.execute(create_predict)


    mydb.commit()
except mysql.connector.Error as err:
    print("Error:", err)

# Close database connection
def close_db_connection():
    if 'mydb' in globals():
        cursor.close()
        mydb.close()


#######################################################################################
######################################## Swagger ######################################
#######################################################################################



@app.route('/swagger.json')
def send_swagger_json():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'swagger.json')


########################################################################################
################################ Price melon Table #####################################
########################################################################################

@app.route('/')
def welcome():
    return 'Welcome my app'


@app.route('/get_all_data')
def get_all_data():
    try:
        # Retrieve all data from MySQL
        select_query = f"SELECT * FROM data.price_prod;"
        cursor.execute(select_query)
        data = cursor.fetchall()

        result = []
        for row in data:

            result.append({
                


                'date_price': str(row[1]),
                'date_create': str(row[2]),
                'id_prod': row[3],
                'minPrice': row[4],
                'maxPrice': row[5],
                'avgPrice': row[6],
                'unit' : row[7]
            })



            

        return make_response(jsonify(result),200)
    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({'error': str(err)}), 500
    

#############################################################################################
##################################### Get by id #############################################
#############################################################################################



@app.route('/get_data_by_product_id/<int:product_id>')
def get_data_by_product_id(product_id):
    try:
        # Execute SQL query
        select_query = "SELECT * FROM data.price_prod WHERE product_id = %s;"
        cursor.execute(select_query, (product_id,))
        
        # Fetch all rows
        data = cursor.fetchall()
        

        if data:
            # Prepare result
            result = []
            for row in data:
                result.append({
                    'date_price': str(row[1]),
                    'date_create': str(row[2]),
                    'product_id': row[3],
                    'minPrice': row[4],
                    'maxPrice': row[5],
                    'avgPrice': row[6],
                    'unit': row[7]
                })
            return jsonify(result), 200
        elif not data:
            return make_response(jsonify({"error":"Not found any product id"}),401)

    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({'error': str(err)}), 500



#############################################################################################
################################ Save new product & price ###################################
#############################################################################################


@app.route('/save_data', methods=['POST'])
def save_data():
    try:
        if request.method == 'POST':
            data = request.get_json()

            # Extract data from the JSON payload
            date_price = data.get('date_price')
            date_create = data.get('date_create')
            name = data.get('name')
            min_price = data.get('minPrice')
            max_price = data.get('maxPrice')
            avg_price = data.get('avgPrice')
            unit = data.get('unit')

            # Check if the product exists in product_detail
            check_product_query = "SELECT id FROM product_detail WHERE name = %s"
            cursor.execute(check_product_query, (name,))
            result = cursor.fetchone()

            if result:
                product_id = result[0]
            else:
                # If the product does not exist, insert it into product_detail
                insert_product_query = "INSERT INTO product_detail (name) VALUES (%s)"
                cursor.execute(insert_product_query, (name,))
                mydb.commit()

                # Get the ID of the newly inserted product
                product_id = cursor.lastrowid

            # Save data to price_prod
            insert_price_query = """
            INSERT INTO price_prod (date_price, date_create, product_id, minPrice, maxPrice, avgPrice,unit)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_price_query, (date_price, date_create, product_id, min_price, max_price, avg_price,unit))
            mydb.commit()

            return jsonify({'message': 'Saved product successfully'})
    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({'error': str(err)}), 500
    


#############################################################################################
############################# Delete all data in table price prod ###########################
#############################################################################################


@app.route('/delete_all_data', methods=['DELETE'])
def delete_all_data():
    try:
        # Delete all data from MySQL
        delete_query = "DELETE FROM data.price_prod;"
        cursor.execute(delete_query)
        mydb.commit()

        return jsonify({'message': 'All data deleted successfully'}), 200

    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({'error': str(err)}), 500




#############################################################################################
##################################### Get all type product ##################################
#############################################################################################


@app.route('/get_all_data_master')
def get_all_data_master():
    try:
        # Retrieve all data from MySQL
        select_query = f"SELECT * FROM data.product_detail;"
        cursor.execute(select_query)
        data = cursor.fetchall()

        result = []
        for row in data:

            result.append({
                # 'no': row[0],


                "id":row[0],
                "name":row[1]
            })



            
        
        return make_response(jsonify(result),200)
    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({'error': str(err)}), 500
    






#######################################################################
########################### API price predict #########################
#######################################################################



@app.route('/getdata_pred/<int:product_id>', methods=['GET'])
def getdata_pred(product_id):
    try:
        select_query_name = f"SELECT * FROM" 
        


        # Retrieve laste 180 data from MySQL
        select_query = f"SELECT * FROM (SELECT minPrice, maxPrice, avgPrice, id, date_price FROM price_prod WHERE product_id = {product_id} ORDER BY date_price DESC  LIMIT 180 ) AS last_180_rows ORDER BY date_price ASC;"              
        cursor.execute(select_query)
        data = cursor.fetchall()
        if not data:
            return make_response(jsonify({'error': 'No data available for the specified product ID'}), 401)


        
        minPrice = []
        maxPrice = []
        for row in data:
            minPrice.append(float(row[0]))
            maxPrice.append(float(row[1]))

        #Reshape data
        x0 = np.array(minPrice.copy(), dtype=np.float32).reshape(-1, 1)
        x1 = np.array(maxPrice.copy(), dtype=np.float32).reshape(-1, 1)

        #Normalize
        scaler = MinMaxScaler(feature_range=(0, 1))
        x_1_scaled = scaler.fit_transform(x0)
        x_2_scaled = scaler.fit_transform(x1)

        
        dataset_stacked = hstack((x_1_scaled,x_2_scaled))

        #reshape data 2 dim 90 row 2 col(min, max)
        test_X = dataset_stacked.reshape((2,90,2))

        #load model
        model  = load_model("no.1_adam_3col.h5")

        #Predict 
        pred  = model.predict(test_X)

        #inverse data 
        y_pred = scaler.inverse_transform(pred)
        
        #Select row 1 and defind type to int
        predict  = np.array(y_pred.copy()[1], dtype=np.int64)
        
        # print(predict)
        json_pred = []
        number = len(predict)
        print(number)
        
        for i in range(number):

            json_pred.append({
                "name":'เมล่อนไทย',
                "date":str(datetime.date.today() + datetime.timedelta(days=i)),
                "price":int(predict[i]),
            })

        return make_response({"data":json_pred},200)
    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({'error': str(err)}), 500
    


@app.route('/get_data_by_date/<date>', methods = ['GET'])
def get_data_by_date(date):
    try:
        select_query = f"SELECT * FROM data.price_prod where date_price = {date}"
        cursor.execute(select_query)
        date = cursor.fetchall()

    except mysql.connector.errors as err:
        return make_response(jsonify({"error": err}))
        

@app.route('/get_laest_data', methods =['GET'])
def get_laest_data():
    try:
        # Retrieve laste 180 data from MySQL
        select_query = f"SELECT date_price, minPrice,maxPrice,avgPrice from price_prod order by date_price desc limit 5;"              
        cursor.execute(select_query)
        data = cursor.fetchall()

        result = []
        for row in data:
            result.append({
                "date_price":str(row[0]),
                "minPrice":row[1],
                "maxPrice":row[2],
                "avgPrice":row[3]
                
            })
        return make_response(result,200)
    except mysql.connector.errors as err:
        return make_response(jsonify({'error': err}),500)
    




if __name__ == '__main__':
    
    app.run(host='0.0.0.0',debug=True, port= os.getenv("flask_port"))
    

