import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

# 파일 경로 (필요 시 수정)
DATA_PATH = "/Users/phaethon/Desktop/Reagan Project/Reagan/DATA/phishing_features.csv"

# 데이터 불러오기
df = pd.read_csv(DATA_PATH)

# 특징 컬럼
features = [
    'url_length',
    'num_hyphens',
    'num_at',
    'has_ip',
    'num_subdirectories',
    'length_subdomain',
    'has_https',
    'is_shortened'
]

X = df[features]
y = df['label']

# 훈련/검증 세트 분리
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = lgb.LGBMClassifier(
    objective='binary',
    boosting_type='gbdt',
    num_leaves=31,
    learning_rate=0.05,
    n_estimators=100,
    random_state=42
)

# 학습
model.fit(X_train, y_train)

# 예측
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

# 평가
print("[결과 요약]")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("ROC AUC:", roc_auc_score(y_test, y_proba))

joblib.dump(model, "/Users/phaethon/Desktop/Reagan Project/Reagan/BACK/detection_ai/lightgbm_model_v01.pkl")
print("모델이 'lightgbm_model.pkl' 파일로 저장되었습니다.")

