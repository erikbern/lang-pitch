import json, numpy, seaborn
from matplotlib import pyplot

by_gender = {}
by_lang = {}

for line in open('clips_analyzed.jsons'):
    try:
        data = json.loads(line.strip())
    except:
        break
    if data['freq'] is not None and not numpy.isnan(data['freq']):
        by_gender.setdefault(data['gender'], []).append(data['freq'])
        by_lang.setdefault(data['lang_code'], []).append(data['freq'])

seaborn.distplot(by_gender['male'], color='blue')
seaborn.distplot(by_gender['female'], color='red')
pyplot.show()

seaborn.distplot(by_lang['en'], color='blue')
seaborn.distplot(by_lang['ja'], color='red')
pyplot.show()
