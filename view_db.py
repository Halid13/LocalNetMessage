#!/usr/bin/env python3
"""
Visualiseur web simple pour les bases de données SQLite
"""

from flask import Flask, render_template_string
import sqlite3
import os

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Visualiseur SQLite</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .container { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .db-section { margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { background: #4CAF50; color: white; padding: 10px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #ddd; }
        tr:hover { background: #f5f5f5; }
        .empty { color: #888; font-style: italic; }
        .count { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Visualiseur des Bases de Données SQLite</h1>
        
        {% for db_name, db_data in databases.items() %}
        <div class="db-section">
            <h2>{{ db_name }}</h2>
            {% if db_data.error %}
                <p class="empty">⚠️ Erreur: {{ db_data.error }}</p>
            {% else %}
                {% for table_name, table_data in db_data.items() %}
                    <h3>{{ table_name }} <span class="count">({{ table_data.count }} lignes)</span></h3>
                    {% if table_data.count > 0 %}
                        <table>
                            <thead>
                                <tr>
                                    {% for col in table_data.columns %}
                                    <th>{{ col }}</th>
                                    {% endfor %}
                                </tr>
                            </thead>
                            <tbody>
                                {% for row in table_data.rows %}
                                <tr>
                                    {% for cell in row %}
                                    <td>{{ cell }}</td>
                                    {% endfor %}
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    {% else %}
                        <p class="empty">Aucune donnée</p>
                    {% endif %}
                {% endfor %}
            {% endif %}
        </div>
        {% endfor %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    databases = {}
    db_files = ['messages.db', 'client_messages.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                
                # Récupérer toutes les tables
                c.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = c.fetchall()
                
                db_data = {}
                for table in tables:
                    table_name = table[0]
                    c.execute(f"SELECT * FROM {table_name}")
                    rows = c.fetchall()
                    columns = [description[0] for description in c.description]
                    
                    db_data[table_name] = {
                        'count': len(rows),
                        'columns': columns,
                        'rows': [tuple(row) for row in rows]
                    }
                
                databases[db_file] = db_data
                conn.close()
            except Exception as e:
                databases[db_file] = {'error': str(e)}
        else:
            databases[db_file] = {'error': 'Fichier non trouvé'}
    
    return render_template_string(HTML_TEMPLATE, databases=databases)

if __name__ == '__main__':
    print("🌐 Ouvrez votre navigateur sur http://localhost:5555")
    app.run(debug=False, port=5555)
