from keras.layers import (
    Input,
    Embedding,
    Dropout,
    SpatialDropout1D,
    Dense,
    Activation,
    BatchNormalization,
    Concatenate,
    Multiply,
    Add
)
from keras.layers.convolutional import Conv1D
from keras.layers.pooling import (
    MaxPooling1D,
    GlobalMaxPooling1D,
    GlobalAveragePooling1D
)

def make_onehot_sequence_input(name, length, n_symbols):
    return Input(
            shape=(length, n_symbols),
            name=name,
            dtype="float32")

def make_index_sequence_input(name, length):
    return Input(
        shape=(length,),
        dtype="int32",
        name=name)

def make_sequence_input(name, length, n_symbols, encoding):
    assert encoding in {"onehot", "index"}
    if encoding == "index":
        return make_index_sequence_input(name, length)
    else:
        return make_onehot_sequence_input(name, length, n_symbols)

def make_numeric_input(name, dim, dtype):
    return Input(name=name, shape=(dim,), dtype=dtype)

def embedding(value, n_symbols, output_dim, dropout=0, initial_weights=None):
    if initial_weights:
        n_rows, n_cols = initial_weights.shape
        if n_rows != n_symbols or n_cols != output_dim:
            raise ValueError(
                "Wrong shape for embedding: expected (%d, %d) but got "
                "(%d, %d)" % (
                    n_symbols, output_dim,
                    n_rows, n_cols))
        embedding_layer = Embedding(
            input_dim=n_symbols,
            output_dim=output_dim,
            mask_zero=False,
            weights=[initial_weights])
    else:
        embedding_layer = Embedding(
            input_dim=n_symbols,
            output_dim=output_dim,
            mask_zero=False)

    value = embedding_layer(value)

    if dropout:
        value = SpatialDropout1D(dropout)(value)

    return value

def conv(value, filter_sizes, output_dim, dropout=0.1):
    """
    Parameters
    ----------
    filter_sizes : int or list of int
        Widths of convolutional filters

    output_dim : int
        Number of filters per width

    dropout : float
        Dropout after convolutional
    """
    if isinstance(filter_sizes, int):
        filter_sizes = [filter_sizes]

    convolved_list = []
    for size in filter_sizes:
        conv_layer = Conv1D(
            filters=output_dim,
            kernel_size=size,
            padding="same")
        convolved = conv_layer(value)
        if dropout:
            # random drop some of the convolutional activations
            convolved = Dropout(dropout)(convolved)

        convolved_list.append(convolved)
    if len(convolved_list) > 1:
        convolved = Concatenate()(convolved_list)
    else:
        convolved = convolved_list[0]
    return convolved

def local_max_pooling(value, size=3, stride=2):
    return MaxPooling1D(pool_size=size, strides=stride)(value)

def global_max_pooling(value):
    return GlobalMaxPooling1D()(value)

def global_mean_pooling(value):
    return GlobalAveragePooling1D()(value)

def global_max_and_mean_pooling(value):
    max_pooled = GlobalMaxPooling1D()(value)
    mean_pooled = GlobalAveragePooling1D(value)
    return Concatenate()([max_pooled, mean_pooled])

def dense_layers(
        value,
        input_size,
        layer_sizes,
        activation="relu",
        init="glorot_uniform",
        batch_normalization=False,
        dropout=0.0):
    for i, dim in enumerate(layer_sizes):
        # hidden layer fully connected layer
        value = Dense(units=dim, kernel_initializer=init)(value)
        value = Activation(activation)(value)

        if batch_normalization:
            value = BatchNormalization()(value)

        if dropout > 0:
            value = Dropout(dropout)(value)
    return value

def merge(values, merge_mode):
    assert merge_mode in {"concat", "add", "multiply"}
    if len(values) == 1:
        return values[0]
    elif merge_mode == "concat":
        return Concatenate()(values)
    elif merge_mode == "add":
        return Add()(values)
    elif merge_mode == "multiply":
        return Multiply()(values)
