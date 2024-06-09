from flask import Flask, request, jsonify
from datetime import datetime
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
generated_order_ids = set()

# Google Sheets setup
scopes = ['https://www.googleapis.com/auth/drive.file']
credentials = ServiceAccountCredentials.from_json_keyfile_name('key.json')
file = gspread.authorize(credentials)
workbook = file.open('OMS')
sheet = workbook.sheet1

@app.route('/', methods=['GET', 'POST'])
def index():
    eligible_pins = ['560037', '560038', '560039', '560040', '560041']
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = {}

    
    #Pincode eligibility check
    def is_pincode_eligible(pincode):
        return pincode in eligible_pins
    
    #Orderid status retrieval
    def get_delivery_status(order_id):
        # Find the row index of the order ID
        order_ids = sheet.col_values(1)  
        try:
            row_index = order_ids.index(order_id) + 1  # Add 1 to convert to 1-based index
        except ValueError:
            return "Not found in our Database. please drop a mail to clientcare@milkdelivery.com. Please type 'hi' to restart conversation "  # Return this message if order ID is not found

        # Read delivery status from the corresponding row
        delivery_status = sheet.cell(row_index, 7).value  # Delivery status in column g
        return delivery_status
    
    data = request.get_json()
    requesttype=data['queryResult']['outputContexts'][1]['parameters']['requesttype']
    
    
 
    
    #Branching starts
    
    if requesttype == 'Order Milk':  
        ordersku = data['queryResult']['outputContexts'][0]['parameters']['Item']
        pincode = str(data['queryResult']['outputContexts'][0]['parameters']['zip-code'])
        phonenumber = str(int(data['queryResult']['outputContexts'][0]['parameters']['number']))
        address = data['queryResult']['outputContexts'][0]['parameters']['address']
        deliverystatus='Received, yet to be updated'
    
        if is_pincode_eligible(pincode):
                #generate new orderid
            while True:
                order_id = ''.join([str(random.randint(0, 9)) for _ in range(7)])
                if order_id not in generated_order_ids:
                    generated_order_ids.add(order_id)
                break

            row_data = [order_id, current_time, ordersku, pincode, phonenumber, address,deliverystatus]
            sheet.append_row(row_data)
            response = {
                'fulfillmentText': f'We have processed your order. Your order id is {order_id}. Please use this to track your order'
                }
        
        else:
            response = {
                'fulfillmentMessages': [
                    {
                        'text': {
                            'text': ["Sorry, the entered pincode is not eligible for delivery right now."]
                            }
                    },
                    {
                        'payload': {
                            'telegram': {
                                'text': "Would you like to try with another address?",
                                'reply_markup': {
                                    'inline_keyboard': [
                                        [
                                            {
                                                'text': 'Yes, I will try with another address',
                                                'callback_data': 'Yes, I will try with another address'
                                                }
                                        ],
                                        [
                                             {
                                                'text': 'No, thank you.',
                                                'callback_data': 'No, thank you.'
                                            }
                                        ]
                                    ]
                                }
                            }
                        }
                    }
                ]
            }


    elif requesttype=='Track Order':
        enquiredorderid=data['queryResult']['parameters']['Enquiredorderid']
        stausofdelivery=get_delivery_status(enquiredorderid)
        response = {
                'fulfillmentText': f'Your order id {enquiredorderid} is {stausofdelivery}'
                }





    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
