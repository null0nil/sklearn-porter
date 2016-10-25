from ..Classifier import Classifier


class MLPClassifier(Classifier):
    """
    See also
    --------
    sklearn.neural_network.MLPClassifier

    http://scikit-learn.org/0.18/modules/generated/sklearn.neural_network.MLPClassifier.html
    """

    SUPPORT = {'predict': ['java']}

    # @formatter:off
    TEMPLATE = {
        'java': {
            'type':     ('{0}'),
            'arr':      ('{{{0}}}'),
            'new_arr':  ('new double[{0}]'),
            'arr[]':    ('double[] {name} = {{{values}}};'),
            'arr[][]':  ('double[][] {name} = {{{values}}};'),
            'arr[][][]': ('double[][][] {name} = {{{values}}};'),
        }
    }
    # @formatter:on


    def __init__(
            self, language='java', method_name='predict', class_name='Tmp'):
        super(MLPClassifier, self).__init__(language, method_name, class_name)


    @property
    def hidden_activation_functions(self):
        """Get a list of supported activation functions of the hidden layers."""
        return ['relu', 'identity', 'tanh']  # 'logistic' failed tests


    @property
    def final_activation_functions(self):
        """Get a list of supported activation functions of the output layer."""
        return ['softmax']  # 'logistic' failed tests


    def port(self, model):
        """
        Port a trained model to the syntax of a chosen programming language.

        Parameters
        ----------
        :param model : MLPClassifier
            An instance of a trained MLPClassifier classifier.
        """
        super(self.__class__, self).port(model)

        # Activation function ('identity', 'logistic', 'tanh' or 'relu'):
        self.hidden_activation = self.model.activation
        if self.hidden_activation not in self.hidden_activation_functions:
            raise ValueError(('The activation function \'%s\' of the model '
                              'is not supported.') % self.hidden_activation)

        # Output activation function ('softmax' or 'logistic'):
        self.final_activation = self.model.out_activation_
        if self.final_activation not in self.final_activation_functions:
            raise ValueError(('The activation function \'%s\' of the model '
                              'is not supported.') % self.final_activation)

        self.n_layers = self.model.n_layers_
        self.n_hidden_layers = self.model.n_layers_ - 2

        self.n_inputs = len(self.model.coefs_[0])
        self.n_outputs = self.model.n_outputs_

        self.hidden_layer_sizes = self.model.hidden_layer_sizes
        if type(self.hidden_layer_sizes) is int:
            self.hidden_layer_sizes = [self.hidden_layer_sizes]
        self.hidden_layer_sizes = list(self.hidden_layer_sizes)

        self.layer_units = \
            [self.n_inputs] + self.hidden_layer_sizes + [self.model.n_outputs_]

        # Weights:
        self.coefficients = self.model.coefs_

        # Bias:
        self.intercepts = self.model.intercepts_

        if self.method_name == 'predict':
            return self.predict()


    def predict(self):
        """
        Port the predict method.

        Returns
        -------
        :return: out : string
            The ported predict method.
        """
        return self.create_class(self.create_method())


    def create_method(self):
        """
        Build the model method or function.

        Returns
        -------
        :return out : string
            The built method as string.
        """

        # Activations:
        activations = list(self._get_activations())
        activations = ', '.join(['atts'] + activations)
        activations = self.temp('arr[][]').format(
            name='activations', values=activations)

        # Coefficients (weights):
        coefficients = []
        for layer in self.coefficients:
            layer_weights = []
            for weights in layer:
                weights = ', '.join([repr(w) for w in weights])
                layer_weights.append(self.temp('arr').format(weights))
            layer_weights = ', '.join(layer_weights)
            coefficients.append(self.temp('arr').format(layer_weights))
        coefficients = ', '.join(coefficients)
        coefficients = self.temp('arr[][][]').format(
            name='coefficients', values=coefficients)

        # Intercepts (biases):
        intercepts = list(self._get_intercepts())
        intercepts = ', '.join(intercepts)
        intercepts = self.temp('arr[][]').format(
            name='intercepts', values=intercepts)

        return self.temp('method').format(
            class_name=self.class_name, method_name=self.method_name,
            n_features=self.n_inputs, n_classes=self.n_outputs,
            activations=activations, coefficients=coefficients,
            intercepts=intercepts)


    def create_class(self, method):
        """
        Build the model class.

        Returns
        -------
        :return out : string
            The built class as string.
        """
        return self.temp('class').format(
            class_name=self.class_name, method_name=self.method_name,
            method=method, n_features=self.n_inputs,
            hidden_activation=self.hidden_activation,
            final_activation=self.final_activation)


    def _get_intercepts(self):
        """
        Concatenate all intercepts of the classifier.
        """
        for layer in self.intercepts:
            inter = ', '.join([repr(b) for b in layer])
            yield self.temp('arr').format(inter)


    def _get_activations(self):
        """
        Concatenate the layers sizes of the classifier except the input layer.
        """
        for layer in self.layer_units[1:]:
            yield self.temp('new_arr').format((str(int(layer))))

