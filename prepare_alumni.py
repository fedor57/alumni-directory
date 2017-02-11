
import ujson
import codecs

data = ujson.decode(open('./alumni.json', 'r').read())

output = codecs.open('./alumni.tsv', 'w', 'utf-8')
for klass in data.values():
    year = str(klass['year'])
    letter = klass['name'][-2]
    for pupil in klass['pupils']:
        output.write(u'\t'.join((pupil, year, letter)) + u'\n')

output.close()

