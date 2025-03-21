import json
import requests
from fastapi import FastAPI
import string
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
genai.configure(api_key="APIKEY")
generation_config = {
  "temperature": 0,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_ONLY_HIGH"
  }
]
model = genai.GenerativeModel(model_name="gemini-pro", generation_config=generation_config,safety_settings=safety_settings)

def get_json_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            return json_data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

def remove_key_value_pairs(json_list, keys_to_remove):
    modified_list = []
    for json_obj in json_list:
        modified_obj = {key: value for key, value in json_obj.items() if key not in keys_to_remove}
        modified_list.append(modified_obj)
    return modified_list

def filter_by_merchant_id(json_list, target_merchant_id):
    filtered_list = [json_obj for json_obj in json_list if json_obj.get("merchant_id") == target_merchant_id]
    return filtered_list
def getProductName(pid):
    products=remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/product/getAllProducts"), ["_id","image"])
    for pdts in products:
        if(pdts.get("product_id")==pid):
            return str(pdts.get('name'))
def find_json_object_by_product_id(json_list, target_product_id):
    for json_obj in json_list:
        if json_obj.get("product_id") == target_product_id:
            return json_obj
    return None




@app.get("/getProductWithMaxProfit")
def api1(merchantId : str):
    modified_json_objects = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/sales/all_sales"), ["_id","date_sold"])
    modified_json_purchases = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/purchase/all_purchases"), ["_id", "date_purchased","total_cost_price","units_purchased","supplier_id"])
    modified_json_objects = filter_by_merchant_id(modified_json_objects, merchantId)
    modified_json_purchases=filter_by_merchant_id(modified_json_purchases,merchantId)
    print(modified_json_objects)
    print("purchases")
    print(modified_json_purchases)
    products=remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/product/getAllProducts"), ["_id","image"])
    prompt_parts = [
        'analyse the given data and tell me which product made the maximum profit for merchant with merchant id ',str(merchantId),'   Data of sales of that particular merchant: ', str(modified_json_objects), 'Data of purchases from supplier of that particular merchant :',str(modified_json_purchases),'Data of all products : ',str(products),'     Just send product name, product id and profit per unit sold, of the pdt with max profit only'
    ]
    return model.generate_content(prompt_parts).text

@app.get("/topProductsSold")
def api2():
    modified_json_objects = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/sales/all_sales")
                                                   , ["_id", "date_sold","selling_price_per_unit","total_selling_price","merchant_id"])
    prompt_parts = [
        'analyse the data about product id and number sold, given below, and tell the the top 3 products which have sold the most', str(modified_json_objects), ' Just send the product id and the total number sold, for the top 3 selling product, in a numbered list format which is easy to read'
    ]
    return model.generate_content(prompt_parts).text

@app.get("/topProductForMaxProfit")
def api3():
    modified_json_objects = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/sales/all_sales")
                                                   , ["_id", "date_sold","merchant_id"])
    print(modified_json_objects)
    prompt_parts = [
        'analyse the data about products sold, given below, and tell me the top 3 products which maximum combined selling price', str(modified_json_objects), ' Just send the product id and total selling price for that product, in a numbered list format and easy to read, top 3 only'
    ]
    return model.generate_content(prompt_parts).text

@app.get("/getBestSuppliers")
def api4(productId : str):
    modified_json_objects = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/suppliers/:0")
, ["_id","shop_name","email","phone","address","product_prices"])
    print(modified_json_objects)
    prompt_parts = [
        'analyse the given data and tell me the suppliers that have the highest average rating from the list named rating and sells the product ',str(productId),' which is present in the array names products_sold. Data in JSON is:', str(modified_json_objects), ' Just send the top 3 highly rated supplier name, selling that particular product'
    ]
    return model.generate_content(prompt_parts).text

@app.get("/getRisks")
def api5(merchantId: str):
    modified_suppliers = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/suppliers/:0")
, ["_id","shop_name","email","phone","address","product_prices"])
    print(modified_suppliers)
    modified_purchases= remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/purchase/all_purchases"), ["_id"])
    print(modified_purchases)
    modified_sales_info = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/sales/all_sales"), ["_id", "date_sold"])
    modified_sales_info = filter_by_merchant_id(modified_sales_info, merchantId)
    prompt_parts = [
        'analyse the given data and tell me if there is any anomaly . ratings of suppliers:   ',str(modified_suppliers),'    and data of merchant purchases from suppliers: ',str(modified_purchases),' and the data of product sales of the merchants:  ',str(modified_sales_info), '     if possible anomaly is found, return the information about that anomalous purchase of merchant',str(merchantId),' only. If no anomaly found, return NOT_FOUND'
    ]
    return model.generate_content(prompt_parts).text

@app.get("/getOptimization")
def api6(merchantId: str):
    modified_suppliers = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/suppliers/:0")
, ["_id","shop_name","email","phone","address","product_prices"])
    print(modified_suppliers)
    modified_purchases= remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/purchase/all_purchases"), ["_id"])
    print(modified_purchases)
    modified_sales_info = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/sales/all_sales"), ["_id", "date_sold"])
    modified_sales_info = filter_by_merchant_id(modified_sales_info, merchantId)
    print(modified_sales_info)
    prompt_parts = [
        'analyse the given data and tell me if the merchant ',str(merchantId),'.Increase his profits by getting goods from another supplier for cheap. Data of information about suppliers:  ',str(modified_suppliers),'    and data of information of merchant purchases from suppliers: ',str(modified_purchases),' and the data of product sales of the merchant:  ',str(modified_sales_info), '     if cheaper suppliers are available, mention all the details for merchant ',str(merchantId),' only. return the data in an easy to read format and only return the top 3 optimizations. If no optimizations are possible, send NOT_FOUND. All numbers are in rupees. make sure that the new cost price should be less than the original cost price after optimization.'
    ]
    return model.generate_content(prompt_parts).text

@app.get("/cheapestSupplier")
def api7(productId: str):
    modified_suppliers = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/suppliers/:0")
, ["_id","shop_name","email","phone","address"])
    print(modified_suppliers)
    prompt_parts = [
        'analyse the data and determine which supplier sells product with product id ',str(productId),' at the cheapest price. Data is',str(modified_suppliers),'    Return the top 3 cheapest suppliers for that particular product, and their prices along with the supplier id and supplier name, who sells it'
    ]
    return model.generate_content(prompt_parts).text

@app.get("/fastestSupplier")
def api8(productId: str):
    modified_suppliers = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/suppliers/:1")
, ["_id","shop_name","email","phone","address"])
    print(modified_suppliers)
    prompt_parts = [
        'analyse the data and determine which supplier sells product with product id ',str(productId),' at the cheapest price. Data is sprted according to delivery speed, data :',str(modified_suppliers),'    Return the top 3 cheapest suppliers for that particular product, and their prices along with the supplier id and supplier name, who sells it'
    ]
    return model.generate_content(prompt_parts).text
@app.get("/monthwiseProfit")
def api8(merchantId: str):
    sp = get_json_data("https://bizminds-backend.onrender.com/api/sales/"+str(merchantId)+"/12months_sales")
    cp = get_json_data("https://bizminds-backend.onrender.com/api/purchase/monthwise/"+str(merchantId))
    print(sp)
    print(cp)
    prompt_parts = [
        "The monthwise cost price data is :"+str(cp)+" and the monthwise selling price data is : "+ str(sp)+" Analyse the given data and find out the monthly profit. Return the data as a python dictionary where the keys are the months January to December and the values are the profits. Give the values, dont give code"
    ]
    l=[]
    x= str(model.generate_content(prompt_parts).text)
    y = x[(x.index('{')):(x.index('}')+1)]
    print(y)
    json_data=json.loads(y)
    for value in json_data.values():
        l.append(int(value))
    return l

@app.get("/getLowStocks")
def api8(merchantId: str):
    inventory_data = remove_key_value_pairs(get_json_data("https://bizminds-backend.onrender.com/api/stocks/inventory/"+merchantId),["_id"])
    print(inventory_data)
    ans=""
    for json_obj in inventory_data:
        for i in range(0,len(json_obj.get('products'))):
            if(json_obj.get('quantity')[i] <=50):
                ans+=json_obj.get('products')[i]
                #ans+=","
                #ans+= getProductName(json_obj.get('products')[i])
                ans+=" , quantity is : "
                ans+= str(json_obj.get('quantity')[i])+"\n"
    if(ans==''):
        return "After analysis, no items were found for merchant" + str(merchantId) + "with quantity less than 50 "
    return "After analysis of Inventory, Items found with low quantity in stock:  \n "+ ans + "\n Merchant "+str(merchantId)+" is advised to purchase these items as soon as possible"
