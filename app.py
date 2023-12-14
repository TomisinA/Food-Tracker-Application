from flask import Flask, render_template, request, g
from datetime import datetime
from db.database import get_db


app = Flask(__name__)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/', methods=['POST', 'GET'])
def index():
    db = get_db()

    if request.method == "POST":
        dt = request.form['date']
        dt = datetime.strptime(dt, "%Y-%m-%d")
        date = datetime.strftime(dt, '%Y%m%d')

        db.execute('insert into log_date (entry_date) values (?)', [date])
        db.commit()

    cur = db.execute('select id, entry_date from log_date order by entry_date')
    results = cur.fetchall()

    tot_cur = db.execute("""select log_date_id, log_date.entry_date, sum(food.protein) as protein, sum(food.carbohydrates) as carbohydrates, 
                         sum(food.fat) as fat, sum(food.calories) as calories from food_date join food on food_date.food_id=food.id 
                         join log_date on food_date.log_date_id=log_date.id group by log_date_id order by log_date.entry_date""")
    
    tot_cur_results = tot_cur.fetchall()

    results = []
    
    for i in tot_cur_results:
        p = {}
        p['pretty_date'] = datetime.strftime(datetime.strptime(str(i['entry_date']), "%Y%m%d"), "%B %d, %Y")
        p['protein'] = i['protein']
        p['carbohydrates'] = i['carbohydrates']
        p['calories'] = i['calories']
        p['fat'] = i['fat']
        p['entry_date'] = i['entry_date']
        p['log_date_id'] = i['log_date_id']
        results.append(p)


    dateResults = [{'entry_date':datetime.strftime(datetime.strptime(str(d['entry_date']), "%Y%m%d"), "%B %d, %Y"),
             'actualDate':d['entry_date']} for d in results]
    return render_template('home.html', dateResults=dateResults, results=results)

@app.route('/delete/<id>', methods=["POST", "GET"])
def deleteFood(id):
    db = get_db()

    if request.method == 'POST':
        db.execute('delete from food where id=?',[id])
        db.commit()

    return food()

    



@app.route('/view/<date>', methods=["POST", "GET"])
def view(date):
    db = get_db()
    cur = db.execute("select id, entry_date from log_date where entry_date = ?", [date])
    d = cur.fetchone()

    if request.method == 'POST':
        db.execute("insert into food_date (food_id, log_date_id) values (?,?)", [request.form['food-select'], d['id']])
        db.commit()


    dateResult = {'entry_date':datetime.strftime(datetime.strptime(str(d['entry_date']), "%Y%m%d"), "%B %d, %Y")}
    food_cur = db.execute("select id, name from food")
    food_cur_results = food_cur.fetchall()

    food_date_cur = db.execute("""select food.name,food.protein, food.carbohydrates,food.fat,food.calories
                                from log_date join food_date on food_date.log_date_id=log_date.id join food on 
                               food.id = food_id where log_date.entry_date=(?)""", [date])
    food_date_cur_results = food_date_cur.fetchall()

    food_date_total = {'protein':0, 'carbohydrates':0, 'fat':0, 'calories':0}

    for food in food_date_cur_results:
        food_date_total['protein'] += food['protein'] 
        food_date_total['carbohydrates'] += food['carbohydrates'] 
        food_date_total['fat'] += food['fat'] 
        food_date_total['calories'] += food['calories'] 

    return render_template('day.html', actualDate=d['entry_date'], dateResult=dateResult, food_cur_results=food_cur_results, 
                           food_date_cur_results=food_date_cur_results, food_date_total=food_date_total)
    return "<h1>{}</h1>".format(result['entry_date'])


    return render_template('day.html')

@app.route('/food', methods=["POST", "GET"])
def food():
    db = get_db()

    if request.method == "POST":
        name = request.form['food-name']
        protein = int(request.form['protein'])
        carbs = int(request.form['carbohydrates'])
        fat = int(request.form['fat'])
        calories = protein*4 + carbs*4 + fat*9


        db.execute("insert into food (name,protein,carbohydrates,fat,calories) values (?,?,?,?,?)", 
                   [name,protein,carbs,fat,calories])
        db.commit()
        #return """<h1>Food name:{} 
        # Protein Count: {} Carbs Count: {} Fat count: {}</h1>""".format(request.form['food-name'],
        #                                                                                       request.form['protein'],
        #                                                                                       request.form['carbohydrates'],request.form['fat'])
    curr = db.execute("select * from food")
    results = curr.fetchall()
    return render_template('add_food.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)