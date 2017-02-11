# N57 Community project

## Import data

    wget http://sch57.ru/people/alumni/data.json
    ./manage.py convert_json data.json --db db.tsv --teachers teachers.tsv
    ./manage.py import_teachers teachers.tsv
    ./manage.py importdb db.tsv
