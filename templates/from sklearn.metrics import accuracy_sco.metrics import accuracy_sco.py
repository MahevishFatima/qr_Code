from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def evaluate_model(metadata, main_output_path):
    y_true = []
    y_pred = []

    for index, row in metadata.iterrows():
        file_name = row['id']
        mfcc_path = os.path.join(main_output_path, "mfcc", f"{file_name}_mfcc.npy")

        try:
            mfcc_features = np.load(mfcc_path)

            if np.isnan(mfcc_features).any() or np.isinf(mfcc_features).any():
                print(f"Error: NaN or infinite values found in MFCC features for {file_name}. Skipping to the next file.")
                continue

            scaler = StandardScaler()
            mfcc_features_scaled = scaler.fit_transform(mfcc_features)

            phoneme_sequence = str(row['phoneme_sequence']).split()

            for phoneme in phoneme_sequence:

                dnn_model_path = os.path.join(main_output_path, "dnn_models", f"{phoneme}_dnn_model.joblib")
                dnn_model = joblib.load(dnn_model_path)

                predicted_labels = dnn_model.predict(mfcc_features_scaled)

                #phoneme_sequence = str(row['phoneme_sequence']).split()
            y_true.extend(phoneme_sequence)
            y_pred.extend(predicted_labels)

        except FileNotFoundError:
            print(f"ERROR: File not found. Skipping to the next file.")
            continue

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')

    print(f"Accuracy: {accuracy}")
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print(f"F1-score: {f1}")

# Assuming 'metadata' is your DataFrame with 'id', 'phoneme_sequence', and 'sentence' columns
evaluate_model(test_metadata, main_output_path)
