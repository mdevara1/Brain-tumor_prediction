'use client';
import { useState, useEffect } from 'react';

export default function Upload() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [prediction, setPrediction] = useState('');
    const [isPreprocessing, setIsPreprocessing] = useState(false);
    const [trainingState, setTrainingState] = useState(0);

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        setSelectedFile(file);

        if (file) {
            setPreview(URL.createObjectURL(file));
        } else {
            setPreview(null);
        }
    };

    const handlePreprocessing = async () => {
        setIsPreprocessing(true);
        const response = await fetch('http://127.0.0.1:5000/start-preprocessing');
        
        if (response.ok) {
            console.log('Preprocessing started');
            checkTrainingStatusOnce(); // Call the training-status API once after starting preprocessing
        } else {
            alert('Error during preprocessing');
            setIsPreprocessing(false); // Re-enable button if there's an error
        }
    };

    const checkTrainingStatusOnce = async () => {
        try {
            const response = await fetch('http://127.0.0.1:5000/training-status');
            const data = await response.json();
            setTrainingState(data.training_state);

            // Check if training is complete
            if (data.training_state === 1) {
                setIsPreprocessing(false); // Re-enable UI for prediction
            } else {
                // If training is still in progress, show message
                alert("Preprocessing is in progress. Please wait until it's done.");
            }
        } catch (error) {
            console.error('Error checking training status:', error);
        }
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (trainingState === 0) {
            alert('Please wait for preprocessing to complete.');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            body: formData,
        });

        const result = await response.json();
        setPrediction(result.prediction);
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600">
            <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
                <h1 className="text-2xl font-semibold text-center text-gray-700">Brain Tumor Detection</h1>

                {/* Preprocessing Button */}
                {trainingState === 0 && (
                    <div className="mt-4 text-center">
                        <button
                            onClick={handlePreprocessing}
                            className="w-full px-4 py-2 text-white bg-blue-500 hover:bg-blue-600 rounded-lg transition duration-200"
                            disabled={isPreprocessing}
                        >
                            {isPreprocessing ? 'Preprocessing...' : 'Start Preprocessing'}
                        </button>
                        {isPreprocessing && (
                            <p className="mt-4 text-sm text-gray-600">
                                Preprocessing started, please wait a few minutes to start prediction.
                            </p>
                        )}
                    </div>
                )}

                {/* Show Form to Upload and Predict only if trainingState is 1 */}
                {trainingState === 1 && (
                    <form onSubmit={handleSubmit} className="mt-6">
                        <label className="block mb-2 text-sm text-gray-600">Upload an Image</label>
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleFileChange}
                            className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
                        />
                        {preview && (
                            <div className="mt-4">
                                <img
                                    src={preview}
                                    alt="Image Preview"
                                    className="w-full h-auto rounded-lg shadow-md"
                                />
                            </div>
                        )}
                        <button
                            type="submit"
                            className="mt-4 w-full px-4 py-2 text-white bg-indigo-500 hover:bg-indigo-600 rounded-lg transition duration-200"
                        >
                            Predict
                        </button>
                    </form>
                )}

                {/* Display Prediction Result */}
                {prediction && (
                    <div className="mt-6 text-center">
                        <h2 className="text-xl font-semibold text-gray-700">Prediction Result</h2>
                        <p className="mt-2 text-lg text-gray-900">{prediction}</p>
                    </div>
                )}
            </div>
        </div>
    );
}
