from flask import Flask, render_template, request
from pymongo import MongoClient
from datetime import datetime, timedelta
app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['Records']

collection = db['Data']

@app.route('/')
def home():
    return render_template('search_form.html')



@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        submit_button = request.form.get('submit_button', None)
        if submit_button == 'search':
            search_term = request.form['search_term']
            incoming_calls = db.Data.count_documents({'source_number': search_term, 'call_type': 'IN'})
            outgoing_calls = db.Data.count_documents({'$or': [{'source_number': search_term}, {'destination_number': search_term}], 'call_type': 'OUT'})
            total_calls = incoming_calls + outgoing_calls
            return render_template('search_results.html', search_term=search_term, incoming_calls=incoming_calls, outgoing_calls=outgoing_calls, total_calls=total_calls)
        elif submit_button == 'reset':
            return render_template('search_form.html')

@app.route('/calls', methods=['GET'])
def calls():
    start_date = datetime.strptime("2021-12-11T00:00:00", "%Y-%m-%dT%H:%M:%S")
    end_date = datetime.strptime("2021-12-12T23:59:59", "%Y-%m-%dT%H:%M:%S")
    
    incoming_results = collection.aggregate([
        {"$match": {"source_number": "8891194331", "call_type": "IN", "timestamp": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": None, "count": {"$sum": 1}, "total_duration": {"$sum": "$duration"}}}
    ])
    
    incoming_calls = 0
    incoming_duration = 0
    for result in incoming_results:
        incoming_calls = result['count']
        incoming_duration = result['total_duration']
    
    outgoing_results = collection.aggregate([
        {"$match": {"destination_number": "8891194331", "call_type": "OUT", "timestamp": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": None, "count": {"$sum": 1}, "total_duration": {"$sum": "$duration"}}}
    ])
    
    outgoing_calls = 0
    outgoing_duration = 0
    for result in outgoing_results:
        outgoing_calls = result['count']
        outgoing_duration = result['total_duration']
    
    return render_template('calls.html', start_date=start_date, end_date=end_date, search_term='8891194331', incoming_calls=incoming_calls, outgoing_calls=outgoing_calls, incoming_duration=incoming_duration, outgoing_duration=outgoing_duration)




@app.route('/frequent_numbers')
def frequent_numbers():
    in_numbers = list(db.Data.aggregate([
        {
            '$match': {'call_type': 'IN'}
        },
        {
            '$group': {
                '_id': '$source_number',
                'count': {'$sum': 1}
            }
        },
        {
            '$sort': {'count': -1}
        }
    ]))

    out_numbers = list(db.Data.aggregate([
        {
            '$match': {'call_type': 'OUT'}
        },
        {
            '$group': {
                '_id': {'$cond': [{'$eq': ['$source_number', '$destination_number']}, '$source_number', '$destination_number']},
                'count': {'$sum': 1}
            }
        },
        {
            '$sort': {'count': -1}
        }
    ]))

    return render_template('frequent_numbers.html', in_numbers=in_numbers, out_numbers=out_numbers)





@app.route('/duration')
def duration():
    in_numbers = list(db.Data.aggregate([
        {
            '$match': {'call_type': 'IN'}
        },
        {
            '$group': {
                '_id': '$source_number',
                'total_duration': {'$sum': {'$toInt': '$duration'}}
            }
        },
        {
            '$sort': {'total_duration': -1}
        }
    ]))

    out_numbers = list(db.Data.aggregate([
        {
            '$match': {'call_type': 'OUT'}
        },
        {
            '$group': {
                '_id': {'$cond': [{'$eq': ['$source_number', '$destination_number']}, '$source_number', '$destination_number']},
                'total_duration': {'$sum': {'$toInt': '$duration'}}
            }
        },
        {
            '$sort': {'total_duration': -1}
        }
    ]))

    return render_template('duration.html', in_numbers=in_numbers, out_numbers=out_numbers)

if __name__ == '__main__':
    app.run(debug=True)



