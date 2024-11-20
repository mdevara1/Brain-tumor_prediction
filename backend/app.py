import numpy as np
import os, io, threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Paths to dataset and model
train_path = '../backend/brain_tumor_dataset/Training'
test_path = '../backend/brain_tumor_dataset/Testing'
model_file_path = './trained_model.h5'
classes = os.listdir(train_path)
num_classes = len(classes)

# Global variables
current_epoch = 0
total_epochs = 30
training_state = 0  
model = None

class CustomTrainingCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        global current_epoch, training_state
        current_epoch = epoch + 1
        if current_epoch == 2:
            training_state = 1
            print("Epoch 2 reached. State updated to '1' (Ready for image uploads and prediction).")
        
        print(f"Epoch {current_epoch}/{total_epochs} completed")


# Preprocessing step
def preprocess_data(data_path):
    data = []
    for i, class_name in enumerate(classes):
        class_path = os.path.join(data_path, class_name)
        for file_name in os.listdir(class_path):
            img = load_img(os.path.join(class_path, file_name), color_mode='rgb', target_size=(150, 150))
            img = img_to_array(img) / 255.0
            data.append([img, i])
    return data


def prepare_data():
    train_data = preprocess_data(train_path)
    test_data = preprocess_data(test_path)

    train_images, train_labels = zip(*train_data)
    test_images, test_labels = zip(*test_data)

    train_labels = to_categorical(train_labels, num_classes=num_classes)
    test_labels = to_categorical(test_labels, num_classes=num_classes)

    train_images = np.array(train_images).reshape(-1, 150, 150, 3)
    test_images = np.array(test_images).reshape(-1, 150, 150, 3)

    return train_test_split(train_images, train_labels, test_size=0.2, random_state=44)


def build_model():
    base_model = tf.keras.applications.DenseNet201(input_shape=(150, 150, 3), include_top=False, weights='imagenet', pooling='avg')
    base_model.trainable = False

    x = tf.keras.layers.Dense(128, activation='relu')(base_model.output)
    output = tf.keras.layers.Dense(num_classes, activation='softmax')(x)

    model = tf.keras.Model(inputs=base_model.input, outputs=output)
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

def train_model():
    global model, training_state

    # Start preprocessing with training_state = 0
    training_state = 0
    
    X_train, X_test, y_train, y_test = prepare_data()
    model = build_model()

    data_aug = ImageDataGenerator(
        horizontal_flip=True,
        vertical_flip=True,
        rotation_range=20,
        zoom_range=0.2,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.1,
        fill_mode="nearest"
    )

    # Start training with training_state = 0
    history = model.fit(
        data_aug.flow(X_train, y_train, batch_size=32),
        validation_data=(X_test, y_test),
        epochs=total_epochs,
        callbacks=[CustomTrainingCallback()],
        verbose=1
    )

    model.save(model_file_path)
    return history, X_test, y_test


@app.route('/training-status', methods=['GET'])
def training_status():
    global current_epoch, total_epochs, training_state
    return jsonify({
        "current_epoch": current_epoch,
        "total_epochs": total_epochs,
        "training_state": training_state  
    }), 200


@app.route('/start-preprocessing', methods=['GET'])
def start_preprocessing_route():
    def background_task():
        global training_state
        training_state = 1  # 1: Preprocessing
        history, X_test, y_test = train_model()
        print("Preprocessing and model training complete!")
    
    threading.Thread(target=background_task).start()
    return jsonify({"message": "Preprocessing and training started in the background"}), 202


@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    img = load_img(io.BytesIO(file.read()), target_size=(150, 150))
    img_array = img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    global model
    if model is None:
        model = tf.keras.models.load_model(model_file_path)

    prediction = model.predict(img_array)
    predicted_class = classes[np.argmax(prediction)]
    
    return jsonify({'prediction': predicted_class})

if __name__ == '__main__':
    app.run(debug=True)
