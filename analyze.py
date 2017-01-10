import bisect, json, numpy, numpy.fft, os, random, requests, scipy.signal, sha, soundfile, subprocess, sys, tempfile
from matplotlib import pyplot

def freq_from_fft(signal, fs):
    # https://gist.github.com/endolith/255291/fb8794f0bc5d4ae98890fcbaa0af58e75f781993
    N = len(signal)

    # Compute Fourier transform of windowed signal
    windowed = signal * scipy.signal.kaiser(N, 100)
    f = numpy.fft.rfft(windowed)
    hz_factor = 1.0 * fs / N
    freqs = numpy.arange(len(f)) * hz_factor


    #    pyplot.plot(freqs[:100], abs(f[:100]))
    #    pyplot.show()
    
    #    i = numpy.argmax(abs(f))
    #    return i * hz_factor
    return numpy.dot(freqs, abs(f)) / numpy.sum(abs(f))


def download(url):
    fn_mp3 = 'clips/%s.mp3' % sha.new(url).hexdigest()
    fn_wav = 'clips/%s.wav' % sha.new(url).hexdigest()
    if not os.path.exists(fn_mp3):
        print 'downloading %s -> %s' % (url, fn_mp3)
        res = requests.get(url)
        f = open(fn_mp3, 'wb')
        f.write(res.content)
        f.close()
    if not os.path.exists(fn_wav):
        print 'converting %s -> %s' % (fn_mp3, fn_wav)
        subprocess.call('ffmpeg -y -i %s -vn -acodec pcm_s16le -ac 1 -ar 44100 -f wav %s' % (fn_mp3, fn_wav), shell=True)
    return fn_wav


def trim(sig, fs, s=0.2):
    samples = int(s * fs)
    c = numpy.cumsum(abs(sig))
    i = numpy.argmax(c[samples:] - c[:-samples])    
    lo, hi = i, i+samples
    return sig[lo:hi]


def butter_bandpass(lowcut, highcut, fs, order=5):
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    # Not sure why a bandpass doesn't work
    b, a = scipy.signal.butter(order, high, btype='high')
    data = scipy.signal.lfilter(b, a, data)
    b, a = scipy.signal.butter(order, low, btype='low')
    data = scipy.signal.lfilter(b, a, data)
    return data


def get_freq(fn):
    try:
        signal, fs = soundfile.read(fn)
        signal = trim(signal, fs)
    except:
        return None
    signal = butter_bandpass_filter(signal, 80., 250., fs)
    return freq_from_fft(signal, fs)

data = [json.loads(line.strip()) for line in open('clips.jsons')]
data.sort(key=lambda l: sha.new(l['url']).hexdigest())

f = open('clips_analyzed.jsons', 'w')
lu2c = {} # (lang, user) to count
urls = set()
for l in data:
    if l['url'] in urls:
        continue
    urls.add(l['url'])
    print l
    lu_key = (l['lang_code'], l['username'])
    if lu2c.get(lu_key, 0) >= 10:
        print 'already has %d recordings by user' % lu2c[lu_key]
        continue
    lu2c[lu_key] = lu2c.get(lu_key, 0) + 1
    if l['origin'].startswith('(Male'):
        gender = 'male'
    elif l['origin'].startswith('(Female'):
        gender = 'female'
    else:
        continue
    fn = download(l['url'])
    freq = get_freq(fn)
    f.write(json.dumps({'fn': fn, 'freq': freq, 'gender': gender, 'lang_code': l['lang_code'], 'lang': l['lang']}) + '\n')



