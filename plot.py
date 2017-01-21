import h5py, numpy, pandas, pycountry, seaborn
from matplotlib import pyplot

def lang_name(lang):
    try:
        return pycountry.languages.get(alpha_2=lang).name
    except KeyError:
        try:
            return pycountry.languages.get(alpha_3=lang).name
        except KeyError:
            return lang

bootstrap_size = 100
hz_factor = 2.0 # TODO: write to h5 file
f = h5py.File('clips.h5', 'r')
df = pandas.DataFrame(dict(lang=[lang_name(l) for l in f['lang']],
                           gender=f['gender'],
                           origin=f['origin'],
                           freqs=[numpy.array(freqs) for freqs in f['freqs']]))
print df['freqs'].shape

def plot_spectrum(df, category, limit):
    def conf_int_bootstrap(x):
        bootstraps = numpy.array([
            numpy.mean(numpy.random.choice(x, len(x), replace=True)) * hz_factor
            for i in range(bootstrap_size)])
        return numpy.percentile(bootstraps, [5, 25, 75, 95], axis=0)
    c = df[category].value_counts()
    top = c.index[c.values >= limit].tolist()
    freqs = df.groupby(category)['freqs'].apply(conf_int_bootstrap).to_dict()
    colors = seaborn.color_palette('hls', len(top))
    for cat, color in zip(top, colors):
        data = freqs[cat]
        pyplot.fill_between(numpy.arange(len(data[0])) * hz_factor, data[0], data[3], color=color + (0.3,), label=cat)
        pyplot.fill_between(numpy.arange(len(data[0])) * hz_factor, data[1], data[2], color=color + (0.5,))
    pyplot.legend()
    pyplot.show()

plot_spectrum(df, 'lang', 4000)
plot_spectrum(df[df['lang'] == 'English'], 'gender', 0)

def plot_comparison(df, category, limit):
    def repr_freq_bootstrap(x):
        bootstraps = [
            numpy.argmax(numpy.mean(numpy.random.choice(x, len(x), replace=True))) * hz_factor
            for i in range(bootstrap_size)]
        return pandas.DataFrame({'reprFreq': bootstraps})

    def repr_freq_mean(x):
        m = numpy.mean(x)
        return numpy.argmax(m) * hz_factor

    c = df[category].value_counts()
    top = c.index[c.values >= limit].tolist()
    freqs = df.groupby(('gender', category))['freqs'].apply(repr_freq_bootstrap)
    freqs.reset_index(inplace=True)
    mean_freqs = df.groupby(('gender', category))['freqs'].apply(repr_freq_mean).to_dict()
    order = sorted(top, key=lambda lang: (mean_freqs[('male', lang)] + mean_freqs[('female', lang)])/2)
    for gender, color in [('male', '#6666ff'), ('female', '#ff6666')]:
        seaborn.stripplot(data=freqs[freqs['gender'] == gender],
                          orient='h',
                          y=category,
                          x='reprFreq',
                          order=order,
                          # showfliers=False,
                          color=color,
                          size=10,
                          alpha=0.10,
                          edgecolor='none')
    pyplot.show()

# plot_spectrum(df[df['lang'] == 'English'], 'gender')
plot_comparison(df, 'lang', 500)
plot_comparison(df[df['lang'] == 'English'], 'origin', 100)
plot_comparison(df[df['lang'] == 'Spanish'], 'origin', 100)
