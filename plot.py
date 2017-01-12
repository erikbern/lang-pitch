import json, numpy, seaborn, pandas
from matplotlib import pyplot

by_gender = {}

# dataframe
langs = []
genders = []
freqs = []
origins = []

for line in open('clips_analyzed.jsons'):
    try:
        data = json.loads(line.strip())
    except:
        break
    if data['freq'] is not None and not numpy.isnan(data['freq']):
        by_gender.setdefault(data['gender'], []).append(data['freq'])
        langs.append(data['lang_code'])
        genders.append(data['gender'])
        freqs.append(data['freq'])
        origins.append(data['origin'])

# distplot of gender freqs
bins = numpy.arange(0, 500, 10)
seaborn.distplot(by_gender['male'], color='blue', bins=bins)
seaborn.distplot(by_gender['female'], color='red', bins=bins)
pyplot.xlim([0, 500])
pyplot.show()

# boxplot of lang freqs
df = pandas.DataFrame(dict(lang=pandas.Series(langs, dtype='category'),
                           gender=pandas.Series(genders, dtype='category'),
                           freq=pandas.Series(freqs)))
c = df['lang'].value_counts()
top_langs = c.index[c.values >= 500].tolist()
mean_freqs = df.groupby(['lang']).mean().to_dict()['freq']
order = sorted(top_langs, key=lambda lang: mean_freqs[lang])
seaborn.violinplot(data=df,
                   x='lang',
                   y='freq',
                   hue='gender',
                   split=True,
                   order=order),
#showfliers=False)
pyplot.ylabel('Pitch (Hz)')
pyplot.show()
