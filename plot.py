import h5py, numpy, pandas, pycountry, seaborn
from matplotlib import pyplot

lookup_fs = [
    # a few languages have the wrong name in pycountry imo
    lambda lang: {'zh': u'Mandarin Chinese',
                  'el': u'Greek',
                  'no': u'Norwegian'}[lang],
    lambda lang: pycountry.languages.get(alpha_2=lang).name,
    lambda lang: pycountry.languages.get(alpha_3=lang).name
]


def lang_name(lang):
    for f in lookup_fs:
        try:
            return f(lang)
        except KeyError:
            pass

bootstrap_size = 1000
hz_factor = 2.0 # TODO: write to h5 file
f = h5py.File('clips.h5', 'r')
df = pandas.DataFrame(dict(lang=[lang_name(l) for l in f['lang']],
                           gender=f['gender'],
                           origin=f['origin'],
                           freqs=[numpy.array(freqs) for freqs in f['freqs']]))
print(df['freqs'].shape)
print(df['lang'].value_counts())

def plot_fft(df, n, fn):
    print('plotting %s' % fn)
    colors = seaborn.color_palette('hls', n)
    fig = pyplot.figure(figsize=(9, 6))
    for row, color in zip(df['freqs'][:n], colors):
        pyplot.plot(numpy.arange(len(row)) * hz_factor, row, color=color)
    pyplot.xlim([0, 500])
    pyplot.xlabel('Frequency (Hz)')
    pyplot.ylabel('FFT coefficient magnitude')
    fig.tight_layout()
    pyplot.savefig(fn, dpi=300)

plot_fft(df[(df['lang'] == 'English') & (df['gender'] == 'female')], 10, 'pics/ffts.png')

def plot_spectrum(df, category, options, ax, colors=None):
    def conf_int_bootstrap(x):
        bootstraps = numpy.array([
            numpy.mean(numpy.random.choice(x, len(x), replace=True)) * hz_factor
            for i in range(bootstrap_size)])
        return numpy.percentile(bootstraps, [5, 25, 75, 95], axis=0)
    freqs = df.groupby(category)['freqs'].apply(conf_int_bootstrap).to_dict()
    if not colors:
        colors = seaborn.color_palette('hls', len(options))
    for cat, color in zip(options, colors):
        data = freqs[cat]
        ax.fill_between(numpy.arange(len(data[0])) * hz_factor, data[0], data[3], color=color + (0.2,), label=cat)
        ax.fill_between(numpy.arange(len(data[0])) * hz_factor, data[1], data[2], color=color + (0.5,))
    ax.legend()
    pyplot.xlim([0, 500])
    pyplot.xlabel('Frequency (Hz)')
    ax.set_ylabel('FFT coefficient magnitude')

def plot_spectrum_simple(df, category, options, title, fn, colors=None):
    print('plotting %s' % fn)
    fig, ax = pyplot.subplots(1, figsize=(9, 4))
    plot_spectrum(df, category, options, ax, colors=colors)
    ax.set_title(title)
    fig.tight_layout()
    pyplot.savefig(fn, dpi=300)

plot_spectrum_simple(df[df['lang'] == 'English'], 'gender', ['female', 'male'], 'Female vs male spakers', 'pics/en_male_vs_female.png', colors=[(1.0, 0.4, 0.4), (0.4, 0.4, 1.0)])
plot_spectrum_simple(df[df['lang'] == 'English'], 'origin', ['United Kingdom', 'United States'], 'UK vs US, female English speakers', 'pics/us_vs_uk.png')
plot_spectrum_simple(df[df['gender'] == 'male'], 'lang', ['English', 'German', 'Swedish'], 'Male spakers, frequency spectrum', 'pics/en_de_sv.png')

def subplot_spectrum_langs(df, languages, fn):
    print('plotting %s' % fn)
    fig, ax = pyplot.subplots(2, sharex=True, figsize=(9, 7))
    plot_spectrum(df[df['gender'] == 'female'], 'lang', languages, ax[0])
    plot_spectrum(df[df['gender'] == 'male'], 'lang', languages, ax[1])
    ax[0].set_title('Female speakers')
    ax[1].set_title('Male speakers')
    fig.subplots_adjust(hspace=0.1)
    fig.tight_layout()
    pyplot.savefig(fn, dpi=300)

subplot_spectrum_langs(df, ['English', 'Spanish', 'Russian'], 'pics/en_es_ru.png')
subplot_spectrum_langs(df, ['Mandarin Chinese', 'Japanese', 'Korean'], 'pics/zh_ja_ko.png')
subplot_spectrum_langs(df, ['Mandarin Chinese', 'Yue Chinese', 'Wu Chinese', 'Min Nan Chinese'], 'pics/zh_yue_wuu_nan.png')
subplot_spectrum_langs(df, ['Swedish', 'Danish', 'Norwegian', 'Finnish'], 'pics/sv_dk_no_fi.png')

def plot_comparison(df, category, limit, fn):
    print('plotting %s' % fn)
    def repr_freq_bootstrap(x):
        bootstraps = [
            numpy.argmax(numpy.mean(numpy.random.choice(x, len(x), replace=True))) * hz_factor
            for i in range(bootstrap_size)]
        return pandas.DataFrame({'reprFreq': bootstraps})

    c = df[category].value_counts()
    top = c.index[c.values >= limit].tolist()
    freqs = df.groupby(('gender', category))['freqs'].apply(repr_freq_bootstrap).reset_index()
    median_freqs = freqs.groupby(('gender', category))['reprFreq'].apply(numpy.median)
    median_freqs_dict = median_freqs.to_dict()
    order = sorted(top, key=lambda lang: (median_freqs_dict[('male', lang)] + median_freqs_dict[('female', lang)])/2)
    fig = pyplot.figure(figsize=(9, 1 + 0.3*len(order)))
    for gender, color in [('male', '#6666ff'), ('female', '#ff6666')]:
        seaborn.stripplot(data=freqs[freqs['gender'] == gender],
                          orient='h',
                          y=category,
                          x='reprFreq',
                          order=order,
                          color=color,
                          size=14,
                          alpha=1.0 * bootstrap_size**-0.75,
                          edgecolor='none')
    seaborn.stripplot(data=median_freqs.to_frame('freq').reset_index(),
                      orient='h',
                      y=category,
                      x='freq',
                      order=order,
                      facecolors='none',
                      size=10,
                      linewidth=2,
                      edgecolor='#000000')
    pyplot.xlim([0, 500])
    pyplot.xlabel('Frequency (Hz)')
    pyplot.ylabel('')
    fig.tight_layout()
    pyplot.savefig(fn, dpi=300)

plot_comparison(df, 'lang', 400, 'pics/languages_comparison.png')
plot_comparison(df[df['lang'] == 'English'], 'origin', 100, 'pics/en_origins_comparison.png')
plot_comparison(df[df['lang'] == 'Spanish'], 'origin', 100, 'pics/sp_origins_comparison.png')
plot_comparison(df[df['lang'] == 'Arabic'], 'origin', 100, 'pics/ar_origins_comparison.png')
plot_comparison(df[df['lang'] == 'French'], 'origin', 100, 'pics/fr_origins_comparison.png')
plot_comparison(df[df['lang'] == 'Portuguese'], 'origin', 100, 'pics/pt_origins_comparison.png')
plot_comparison(df[df['lang'] == 'German'], 'origin', 100, 'pics/de_origins_comparison.png')

