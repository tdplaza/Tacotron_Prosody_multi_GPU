import librosa
import librosa.filters
from scipy.io import wavfile
from Utils.Hyperparams import hparams
import os
import numpy as np
import tensorflow as tf
import librosa.display as dsp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from Utils.Plot import split_title_line

def resample_wav(input_wav_files, output_dir=None, sample_rate=hparams.sample_rate):
    for file in os.listdir(input_wav_files):
        if file.endswith('.wav'):
            new_sound, original_sample_rate = librosa.load(input_wav_files + file, sample_rate)
            if output_dir is None:
                output_dir = os.path.join(input_wav_files, 'resampled\\')
                os.makedirs(output_dir, exist_ok=True)
            try:
                librosa.output.write_wav(output_dir + file, new_sound, sample_rate)
            except PermissionError:
                raise ('Could not write wav file, check folder permission!')



def split_func(x, split_pos):
    rst = []
    start = 0
    # x will be a numpy array with the contents of the placeholder below
    for i in range(split_pos.shape[0]):
        rst.append(x[:,start:start+split_pos[i]])
        start += split_pos[i]
    return rst

def shape_list(x):
    """Return list of dims, statically where possible."""
    x = tf.convert_to_tensor(x)

    # If unknown rank, return dynamic shape
    if x.get_shape().dims is None:
        return tf.shape(x)

    static = x.get_shape().as_list()
    shape = tf.shape(x)

    ret = []
    for i in range(len(static)):
        dim = static[i]
        if dim is None:
            dim = shape[i]
        ret.append(dim)
    return ret




def hparams_to_string():
    values = hparams.values()
    hp = ['  %s: %s' % (name, values[name]) for name in sorted(values)]
    return 'Hyperparameters:\n' + '\n'.join(hp)


def _assert_valid_input_type(s):
    assert s == 'mulaw-quantize' or s == 'mulaw' or s == 'raw'



def is_mulaw_quantize(s):
    _assert_valid_input_type(s)
    return s == 'mulaw-quantize'


def is_mulaw(s):
    _assert_valid_input_type(s)
    return s == 'mulaw'


def is_raw(s):
    _assert_valid_input_type(s)
    return s == 'raw'


def is_scalar_input(s):
    return is_raw(s) or is_mulaw(s)


# From https://github.com/r9y9/nnmnkwii/blob/master/nnmnkwii/preprocessing/generic.py
def mulaw(x, mu=256):
    """Mu-Law companding
	Method described in paper [1]_.
	.. math::
		f(x) = sign(x) ln (1 + mu |x|) / ln (1 + mu)
	Args:
		x (array-like): Input signal. Each value of input signal must be in
		  range of [-1, 1].
		mu (number): Compression parameter ``μ``.
	Returns:
		array-like: Compressed signal ([-1, 1])
	See also:
		:func:`nnmnkwii.preprocessing.inv_mulaw`
		:func:`nnmnkwii.preprocessing.mulaw_quantize`
		:func:`nnmnkwii.preprocessing.inv_mulaw_quantize`
	.. [1] Brokish, Charles W., and Michele Lewis. "A-law and mu-law companding
		implementations using the tms320c54x." SPRA163 (1997).
	"""
    mu -= 1
    return _sign(x) * _log1p(mu * _abs(x)) / _log1p(mu)


def inv_mulaw(y, mu=256):
    """Inverse of mu-law companding (mu-law expansion)
	.. math::
		f^{-1}(x) = sign(y) (1 / mu) (1 + mu)^{|y|} - 1)
	Args:
		y (array-like): Compressed signal. Each value of input signal must be in
		  range of [-1, 1].
		mu (number): Compression parameter ``μ``.
	Returns:
		array-like: Uncomprresed signal (-1 <= x <= 1)
	See also:
		:func:`nnmnkwii.preprocessing.inv_mulaw`
		:func:`nnmnkwii.preprocessing.mulaw_quantize`
		:func:`nnmnkwii.preprocessing.inv_mulaw_quantize`
	"""
    mu -= 1
    return _sign(y) * (1.0 / mu) * ((1.0 + mu) ** _abs(y) - 1.0)


def mulaw_quantize(x, mu=256):
    """Mu-Law companding + quantize
	Args:
		x (array-like): Input signal. Each value of input signal must be in
		  range of [-1, 1].
		mu (number): Compression parameter ``μ``.
	Returns:
		array-like: Quantized signal (dtype=int)
		  - y ∈ [0, mu] if x ∈ [-1, 1]
		  - y ∈ [0, mu) if x ∈ [-1, 1)
	.. note::
		If you want to get quantized values of range [0, mu) (not [0, mu]),
		then you need to provide input signal of range [-1, 1).
	Examples:
		# >>> from scipy.io import wavfile
		# >>> import pysptk
		# >>> import numpy as np
		# >>> from nnmnkwii import preprocessing as P
		# >>> fs, x = wavfile.read(pysptk.util.example_audio_file())
		# >>> x = (x / 32768.0).astype(np.float32)
		# >>> y = P.mulaw_quantize(x)
		# # >>> print(y.min(), y.max(), y.dtype)
		15 246 int64
	See also:
		:func:`nnmnkwii.preprocessing.mulaw`
		:func:`nnmnkwii.preprocessing.inv_mulaw`
		:func:`nnmnkwii.preprocessing.inv_mulaw_quantize`
	"""
    mu -= 1
    y = mulaw(x, mu)
    # scale [-1, 1] to [0, mu]
    return _asint((y + 1) / 2 * mu)


def inv_mulaw_quantize(y, mu=256):
    """Inverse of mu-law companding + quantize
	Args:
		y (array-like): Quantized signal (∈ [0, mu]).
		mu (number): Compression parameter ``μ``.
	Returns:
		array-like: Uncompressed signal ([-1, 1])
	Examples:
		# >>> from scipy.io import wavfile
		# >>> import pysptk
		# >>> import numpy as np
		# >>> from nnmnkwii import preprocessing as P
		# >>> fs, x = wavfile.read(pysptk.util.example_audio_file())
		# >>> x = (x / 32768.0).astype(np.float32)
		# >>> x_hat = P.inv_mulaw_quantize(P.mulaw_quantize(x))
		# >>> x_hat = (x_hat * 32768).astype(np.int16)
	See also:
		:func:`nnmnkwii.preprocessing.mulaw`
		:func:`nnmnkwii.preprocessing.inv_mulaw`
		:func:`nnmnkwii.preprocessing.mulaw_quantize`
	"""
    # [0, m) to [-1, 1]
    mu -= 1
    y = 2 * _asfloat(y) / mu - 1
    return inv_mulaw(y, mu)




def _sign(x):
    # wrapper to support tensorflow tensors/numpy arrays
    isnumpy = isinstance(x, np.ndarray)
    isscalar = np.isscalar(x)
    return np.sign(x) if (isnumpy or isscalar) else tf.sign(x)


def _log1p(x):
    # wrapper to support tensorflow tensors/numpy arrays
    isnumpy = isinstance(x, np.ndarray)
    isscalar = np.isscalar(x)
    return np.log1p(x) if (isnumpy or isscalar) else tf.log1p(x)


def _abs(x):
    # wrapper to support tensorflow tensors/numpy arrays
    isnumpy = isinstance(x, np.ndarray)
    isscalar = np.isscalar(x)
    return np.abs(x) if (isnumpy or isscalar) else tf.abs(x)


def _asint(x):
    # wrapper to support tensorflow tensors/numpy arrays
    isnumpy = isinstance(x, np.ndarray)
    isscalar = np.isscalar(x)
    return x.astype(np.int) if isnumpy else int(x) if isscalar else tf.cast(x, tf.int32)


def _asfloat(x):
    # wrapper to support tensorflow tensors/numpy arrays
    isnumpy = isinstance(x, np.ndarray)
    isscalar = np.isscalar(x)
    return x.astype(np.float32) if isnumpy else float(x) if isscalar else tf.cast(x, tf.float32)


def sequence_mask(input_lengths, max_len=None, expand=True):
    if max_len is None:
        max_len = tf.reduce_max(input_lengths)
    if expand:
        return tf.expand_dims(tf.sequence_mask(input_lengths, max_len, dtype=tf.float32), axis=-1)
    return tf.sequence_mask(input_lengths, max_len, dtype=tf.float32)


def waveplot(path, y_hat, y_target, hparams):
    sr = hparams.sample_rate

    plt.figure(figsize=(12, 4))
    if y_target is not None:
        ax = plt.subplot(2, 1, 1)
        dsp.waveplot(y_target, sr=sr)
        ax.set_title('Target waveform')
        ax = plt.subplot(2, 1, 2)
        dsp.waveplot(y_hat, sr=sr)
        ax.set_title('Prediction waveform')
    else:
        ax = plt.subplot(1, 1, 1)
        dsp.waveplot(y_hat, sr=sr)
        ax.set_title('Generated waveform')

    plt.tight_layout()
    plt.savefig(path, format="png")
    plt.close()


######################## AUDIO UTILITIES#################################

def load_wav(path, sr):
    return librosa.core.load(path, sr=sr)[0]


def save_wav(wav, path, sr):
    wav *= 32767 / max(0.01, np.max(np.abs(wav)))
    # proposed by @dsmiller
    wavfile.write(path, sr, wav.astype(np.int16))


def save_wavenet_wav(wav, path, sr):
    librosa.output.write_wav(path, wav, sr=sr)


# From https://github.com/r9y9/Wavenet_vocoder/blob/master/audio.py
def start_and_end_indices(quantized, silence_threshold=2):
    for start in range(quantized.size):
        if abs(quantized[start] - 127) > silence_threshold:
            break
    for end in range(quantized.size - 1, 1, -1):
        if abs(quantized[end] - 127) > silence_threshold:
            break

    assert abs(quantized[start] - 127) > silence_threshold
    assert abs(quantized[end] - 127) > silence_threshold

    return start, end


def trim_silence(wav, hparams):
    '''Trim leading and trailing silence

    Useful for M-AILABS dataset if we choose to trim the extra 0.5 silence at beginning and end.
    '''
    # Thanks @begeekmyfriend and @lautjy for pointing out the params contradiction. These params are separate and tunable per dataset.
    return librosa.effects.trim(wav, top_db=hparams.trim_top_db, frame_length=hparams.trim_fft_size,
                                hop_length=hparams.trim_hop_size)[0]


def get_hop_size(hparams):
    hop_size = hparams.hop_size
    if hop_size is None:
        assert hparams.frame_shift_ms is not None
        hop_size = int(hparams.frame_shift_ms / 1000 * hparams.sample_rate)
    return hop_size


def _lws_processor(hparams):
    import lws
    return lws.lws(hparams.n_fft, get_hop_size(hparams), fftsize=hparams.win_size, mode="speech")


def _griffin_lim(S, hparams):
    '''librosa implementation of Griffin-Lim
    Based on https://github.com/librosa/librosa/issues/434
    '''
    angles = np.exp(2j * np.pi * np.random.rand(*S.shape))
    S_complex = np.abs(S).astype(np.complex)
    y = _istft(S_complex * angles, hparams)
    for i in range(hparams.griffin_lim_iters):
        angles = np.exp(1j * np.angle(_stft(y, hparams)))
        y = _istft(S_complex * angles, hparams)
    return y


def _stft(y, hparams):
    ''' short time Fourier transform (STFT)
    Transform audio file to complex-valued matrix
    input: time series form of audio file
    output: STFT matrix (numpy array)'''
    if hparams.use_lws:
        return _lws_processor(hparams).stft(y).T
    else:
        return librosa.stft(y=y, n_fft=hparams.n_fft, hop_length=get_hop_size(hparams), win_length=hparams.win_size)


def _istft(y, hparams):
    '''Inverse STFT
    Transform STFT matrix back to time series
    input STFT matrix
    output time series 1 dimensional numpy array'''
    return librosa.istft(y, hop_length=get_hop_size(hparams), win_length=hparams.win_size)


def num_frames(length, fsize, fshift):
    """Compute number of time frames of spectrogram
    """
    pad = (fsize - fshift)
    if length % fshift == 0:
        M = (length + pad * 2 - fsize) // fshift + 1
    else:
        M = (length + pad * 2 - fsize) // fshift + 2
    return M


def pad_lr(x, fsize, fshift):
    """Compute left and right padding
    """
    M = num_frames(len(x), fsize, fshift)
    pad = (fsize - fshift)
    T = len(x) + 2 * pad
    r = (M - 1) * fshift + fsize - T
    return pad, pad + r


# Conversions
_mel_basis = None
_inv_mel_basis = None


def _linear_to_mel(spectrogram, hparams):
    global _mel_basis
    if _mel_basis is None:
        _mel_basis = _build_mel_basis(hparams)
    return np.dot(_mel_basis, spectrogram)


def _mel_to_linear(mel_spectrogram, hparams):
    global _inv_mel_basis
    if _inv_mel_basis is None:
        _inv_mel_basis = np.linalg.pinv(_build_mel_basis(hparams))
    return np.maximum(1e-10, np.dot(_inv_mel_basis, mel_spectrogram))


def _build_mel_basis(hparams):
    assert hparams.fmax <= hparams.sample_rate // 2
    return librosa.filters.mel(hparams.sample_rate, hparams.n_fft, n_mels=hparams.num_mels,
                               fmin=hparams.fmin, fmax=hparams.fmax)


def _amp_to_db(x, hparams):
    min_level = np.exp(hparams.min_level_db / 20 * np.log(10))
    return 20 * np.log10(np.maximum(min_level, x))


def _db_to_amp(x):
    return np.power(10.0, (x) * 0.05)


def _normalize(S, hparams):
    if hparams.allow_clipping_in_normalization:
        if hparams.symmetric_mels:
            return np.clip((2 * hparams.max_abs_value) * (
                    (S - hparams.min_level_db) / (-hparams.min_level_db)) - hparams.max_abs_value,
                           -hparams.max_abs_value, hparams.max_abs_value)
        else:
            return np.clip(hparams.max_abs_value * ((S - hparams.min_level_db) / (-hparams.min_level_db)), 0,
                           hparams.max_abs_value)

    assert S.max() <= 0 and S.min() - hparams.min_level_db >= 0
    if hparams.symmetric_mels:
        return (2 * hparams.max_abs_value) * (
                (S - hparams.min_level_db) / (-hparams.min_level_db)) - hparams.max_abs_value
    else:
        return hparams.max_abs_value * ((S - hparams.min_level_db) / (-hparams.min_level_db))


def _denormalize(D, hparams):
    if hparams.allow_clipping_in_normalization:
        if hparams.symmetric_mels:
            return (((np.clip(D, -hparams.max_abs_value,
                              hparams.max_abs_value) + hparams.max_abs_value) * -hparams.min_level_db / (
                             2 * hparams.max_abs_value))
                    + hparams.min_level_db)
        else:
            return ((np.clip(D, 0,
                             hparams.max_abs_value) * -hparams.min_level_db / hparams.max_abs_value) + hparams.min_level_db)

    if hparams.symmetric_mels:
        return (((D + hparams.max_abs_value) * -hparams.min_level_db / (
                2 * hparams.max_abs_value)) + hparams.min_level_db)
    else:
        return ((D * -hparams.min_level_db / hparams.max_abs_value) + hparams.min_level_db)


def _round_up_tf(x, multiple):
    # Tf version of remainder = x % multiple
    remainder = tf.mod(x, multiple)
    # Tf version of return x if remainder == 0 else x + multiple - remainder
    x_round = tf.cond(tf.equal(remainder, tf.zeros(tf.shape(remainder), dtype=tf.int32)),
                      lambda: x,
                      lambda: x + multiple - remainder)

    return x_round
#
#
# def MaskedMSE(targets, outputs, targets_lengths, hparams, mask=None):
#     '''Computes a masked Mean Squared Error
# 	'''
#
#     # [batch_size, time_dimension, 1]
#     # example:
#     # sequence_mask([1, 3, 2], 5) = [[[1., 0., 0., 0., 0.]],
#     #							    [[1., 1., 1., 0., 0.]],
#     #							    [[1., 1., 0., 0., 0.]]]
#     # Note the maxlen argument that ensures mask shape is compatible with r>1
#     # This will by default mask the extra paddings caused by r>1
#     if mask is None:
#         mask = sequence_mask(targets_lengths, hparams.outputs_per_step, True)
#
#     # [batch_size, time_dimension, channel_dimension(mels)]
#     ones = tf.ones(shape=[tf.shape(mask)[0], tf.shape(mask)[1], tf.shape(targets)[-1]], dtype=tf.float32)
#     mask_ = mask * ones
#
#     with tf.control_dependencies([tf.assert_equal(tf.shape(targets), tf.shape(mask_))]):
#         return tf.losses.mean_squared_error(labels=targets, predictions=outputs, weights=mask_)
#
#
# def MaskedSigmoidCrossEntropy(targets, outputs, targets_lengths, hparams, mask=None):
#     '''Computes a masked SigmoidCrossEntropy with logits
# 	'''
#
#     # [batch_size, time_dimension]
#     # example:
#     # sequence_mask([1, 3, 2], 5) = [[1., 0., 0., 0., 0.],
#     #							    [1., 1., 1., 0., 0.],
#     #							    [1., 1., 0., 0., 0.]]
#     # Note the maxlen argument that ensures mask shape is compatible with r>1
#     # This will by default mask the extra paddings caused by r>1
#     if mask is None:
#         mask = sequence_mask(targets_lengths, hparams.outputs_per_step, False)
#
#     with tf.control_dependencies([tf.assert_equal(tf.shape(targets), tf.shape(mask))]):
#         # Use a weighted sigmoid cross entropy to measure the <stop_token> loss. Set hparams.cross_entropy_pos_weight to 1
#         # will have the same effect as  vanilla tf.nn.sigmoid_cross_entropy_with_logits.
#         losses = tf.nn.weighted_cross_entropy_with_logits(targets=targets, logits=outputs,
#                                                           pos_weight=hparams.cross_entropy_pos_weight)
#
#     with tf.control_dependencies([tf.assert_equal(tf.shape(mask), tf.shape(losses))]):
#         masked_loss = losses * mask
#
#     return tf.reduce_sum(masked_loss) / tf.count_nonzero(masked_loss, dtype=tf.float32)
def MaskedMSE(targets, outputs, targets_lengths, hparams, mask=None):
    '''Computes a masked Mean Squared Error
    '''

    #[batch_size, time_dimension, 1]
    #example:
    #sequence_mask([1, 3, 2], 5) = [[[1., 0., 0., 0., 0.]],
    #							    [[1., 1., 1., 0., 0.]],
    #							    [[1., 1., 0., 0., 0.]]]
    #Note the maxlen argument that ensures mask shape is compatible with r>1
    #This will by default mask the extra paddings caused by r>1
    if mask is None:
        mask = sequence_mask(targets_lengths, hparams.outputs_per_step, True)

    #[batch_size, time_dimension, channel_dimension(mels)]
    ones = tf.ones(shape=[tf.shape(mask)[0], tf.shape(mask)[1], tf.shape(targets)[-1]], dtype=tf.float32)
    mask_ = mask * ones

    with tf.control_dependencies([tf.assert_equal(tf.shape(targets), tf.shape(mask_))]):
        return tf.losses.mean_squared_error(labels=targets, predictions=outputs, weights=mask_)

def MaskedSigmoidCrossEntropy(targets, outputs, targets_lengths, hparams, mask=None):
    '''Computes a masked SigmoidCrossEntropy with logits
    '''

    #[batch_size, time_dimension]
    #example:
    #sequence_mask([1, 3, 2], 5) = [[1., 0., 0., 0., 0.],
    #							    [1., 1., 1., 0., 0.],
    #							    [1., 1., 0., 0., 0.]]
    #Note the maxlen argument that ensures mask shape is compatible with r>1
    #This will by default mask the extra paddings caused by r>1
    if mask is None:
        mask = sequence_mask(targets_lengths, hparams.outputs_per_step, False)

    with tf.control_dependencies([tf.assert_equal(tf.shape(targets), tf.shape(mask))]):
        #Use a weighted sigmoid cross entropy to measure the <stop_token> loss. Set hparams.cross_entropy_pos_weight to 1
        #will have the same effect as  vanilla tf.nn.sigmoid_cross_entropy_with_logits.
        losses = tf.nn.weighted_cross_entropy_with_logits(targets=targets, logits=outputs, pos_weight=hparams.cross_entropy_pos_weight)

    with tf.control_dependencies([tf.assert_equal(tf.shape(mask), tf.shape(losses))]):
        masked_loss = losses * mask

    return tf.reduce_sum(masked_loss) / tf.count_nonzero(masked_loss, dtype=tf.float32)


class ValueWindow():
    def __init__(self, window_size=100):
        self._window_size = window_size
        self._values = []

    def append(self, x):
        self._values = self._values[-(self._window_size - 1):] + [x]

    @property
    def sum(self):
        return sum(self._values)

    @property
    def count(self):
        return len(self._values)

    @property
    def average(self):
        return self.sum / max(1, self.count)

    def reset(self):
        self._values = []


def _prepare_mel_targets(targets, alignment):
    max_len = max([len(t) for t in targets])
    return np.stack([_pad_array(t, _round_up(max_len, alignment)) for t in targets])


def _pad_array(array, length, pad_char=-0.1):
    return np.pad(array, [(0, length - array.shape[0]), (0, 0)], mode='constant', constant_values=pad_char)


def _round_up(x, multiple):
    remainder = x % multiple
    return x if remainder == 0 else x + multiple - remainder


def _prepare_inputs(inputs):
    max_len = max([len(x) for x in inputs])
    return np.stack([_pad_input(x, max_len) for x in inputs])


def _pad_input(x, length, pad_char=0):
    return np.pad(x, (0, length - x.shape[0]), mode='constant', constant_values=pad_char)


def get_shapes(x):
    """Return list of dims, statically where possible."""
    x = tf.convert_to_tensor(x)

    # If unknown rank, return dynamic shape
    if x.get_shape().dims is None:
        return tf.shape(x)

    static = x.get_shape().as_list()
    shape = tf.shape(x)

    shapes = []
    for i in range(len(static)):
        dim = static[i]
        if dim is None:
            dim = shape[i]
        shapes.append(dim)
    return shapes


def plot_spectrogram(pred_spectrogram, path, title=None, split_title=False, target_spectrogram=None, max_len=None, auto_aspect=False):
    if max_len is not None:
        target_spectrogram = target_spectrogram[:max_len]
        pred_spectrogram = pred_spectrogram[:max_len]

    if split_title:
        title = split_title_line(title)

    fig = plt.figure(figsize=(10, 8))
    # Set common labels
    fig.text(0.5, 0.18, title, horizontalalignment='center', fontsize=16)

    #target spectrogram subplot
    if target_spectrogram is not None:
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)

        if auto_aspect:
            im = ax1.imshow(np.rot90(target_spectrogram), aspect='auto', interpolation='none')
        else:
            im = ax1.imshow(np.rot90(target_spectrogram), interpolation='none')
        ax1.set_title('Target Mel-Spectrogram')
        fig.colorbar(mappable=im, shrink=0.65, orientation='horizontal', ax=ax1)
        ax2.set_title('Predicted Mel-Spectrogram')
    else:
        ax2 = fig.add_subplot(211)

    if auto_aspect:
        im = ax2.imshow(np.rot90(pred_spectrogram), aspect='auto', interpolation='none')
    else:
        im = ax2.imshow(np.rot90(pred_spectrogram), interpolation='none')
    fig.colorbar(mappable=im, shrink=0.65, orientation='horizontal', ax=ax2)

    plt.tight_layout()
    plt.savefig(path, format='png')
    plt.close()


