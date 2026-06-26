"""
ml_models/train_models.py
Standalone script to train and save all four ML classifiers.
Run from project root: python ml_models/train_models.py
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

from app.utils.ml_engine import MLEngine

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("\n" + "="*60)
    print("  CreditPredict AI — ML Model Training Script")
    print("="*60 + "\n")

    engine = MLEngine(MODELS_DIR)
    metrics = engine.train_and_save()

    print("\n📊 Training Results:")
    print("-" * 60)
    for model_name, m in metrics.items():
        print(f"  {model_name.replace('_',' ').title():<25} "
              f"Acc: {m['accuracy']:>6.2f}%  "
              f"F1: {m['f1_score']:>6.2f}%  "
              f"AUC: {m.get('auc_roc','N/A')!s:>6}%  "
              f"Train: {m['train_time_s']:>5.2f}s")
    print("-" * 60)
    best = max(metrics.items(), key=lambda x: x[1]['accuracy'])
    print(f"\n✅ Best model: {best[0].replace('_',' ').title()} ({best[1]['accuracy']:.2f}% accuracy)")
    print(f"📁 Models saved to: {MODELS_DIR}\n")

if __name__ == '__main__':
    main()
