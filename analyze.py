import h5py, json, numpy, numpy.fft, os, requests, scipy.signal, sha, soundfile, subprocess, traceback
from matplotlib import pyplot

def freq_from_fft(signal, fs):
    # https://gist.github.com/endolith/255291/fb8794f0bc5d4ae98890fcbaa0af58e75f781993
    # Compute Fourier transform of windowed signal
    windowed = signal * scipy.signal.kaiser(len(signal), 14)
    f = numpy.fft.rfft(windowed)
    hz_factor = 1.0 * fs / len(signal)
    return f, hz_factor


def download(url, h, fs=22050):
    fn_mp3 = 'clips/%s.mp3' % h
    fn_wav = 'clips/%s.wav' % h
    if not os.path.exists(fn_mp3):
        print 'downloading %s -> %s' % (url, fn_mp3)
        res = requests.get(url)
        f = open(fn_mp3, 'wb')
        f.write(res.content)
        f.close()
    if not os.path.exists(fn_wav):
        print 'converting %s -> %s' % (fn_mp3, fn_wav)
        subprocess.call('ffmpeg -y -i %s -vn -acodec pcm_s16le -ac 1 -ar %d -f wav %s' % (fn_mp3, fs, fn_wav), shell=True)
    return fn_wav


def trim(sig, fs, s):
    samples = int(s * fs)
    c = numpy.cumsum(abs(sig))
    i = numpy.argmax(c[samples:] - c[:-samples])    
    lo, hi = i, i+samples
    return sig[lo:hi]


def butter_bandpass_filter(data, lowcut, highcut, fs, order=3):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    # Not sure why a bandpass doesn't work
    b, a = scipy.signal.butter(order, high, btype='low')
    data = scipy.signal.lfilter(b, a, data)
    b, a = scipy.signal.butter(order, low, btype='high')
    data = scipy.signal.lfilter(b, a, data)
    return data


def get_signal(fn, trim_s=0.5):
    try:
        signal, fs = soundfile.read(fn)
        signal = butter_bandpass_filter(signal, 50., 300., fs)
        signal = trim(signal, fs, trim_s)
        assert len(signal) == int(fs * trim_s)
    except:
        traceback.print_exc()
        return None
    return signal

cur_files = set([fn.split('.')[0] for fn in os.listdir('clips') if fn.endswith('.wav')])
data = []
for line in open('clips.jsons'):
    try:
        data.append(json.loads(line.strip()))
    except:
        print(line)
for d in data:
    d['hash'] = sha.new(d['url']).hexdigest()
data.sort(key=lambda d: (1-int(d['hash'] in cur_files), d['hash']))

f = open('clips_analyzed_2.jsons', 'w')
lu2c = {} # (lang, user) to count
urls = set()
fs = 22050
trim_s = 2.0
n_freqs = 500
df = []

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
    if ' from ' in l['origin']:
        origin = l['origin'].split(' from ')[1].rstrip(')')
    else:
        continue
    lang = l['lang_code']

    fn = download(l['url'], l['hash'])
    signal = get_signal(fn)
    if signal is not None:
        freqs, hz_factor = freq_from_fft(signal, fs)
        df.append((lang, gender, origin, abs(freqs[:n_freqs])))

with h5py.File('clips.h5', 'w') as f:
    for j, column in enumerate(['lang', 'gender', 'origin']):
        f.create_dataset(column, data=[row[j].encode('utf-8') for row in df], dtype=h5py.special_dtype(vlen=bytes))
    f.create_dataset('freqs', data=numpy.array([row[3] for row in df]))
