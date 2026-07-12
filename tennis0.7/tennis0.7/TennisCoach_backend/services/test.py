"""
模型诊断脚本
用于检查 tennis_rnn_converted.keras 是否正常工作
"""
import keras
import numpy as np
import sys

model_path = sys.argv[1] if len(sys.argv) > 1 else "tennis_rnn_converted.keras"

print(f"加载模型: {model_path}")
model = keras.saving.load_model(model_path)

print("\n========== 模型信息 ==========")
model.summary()

print("\n========== 模型配置 ==========")
print(f"输入 shape: {model.input_shape}")
print(f"输出 shape: {model.output_shape}")
print(f"层数: {len(model.layers)}")

print("\n========== 测试推理 ==========")

# 测试1: 全0输入
test1 = np.zeros((1, 30, 26), dtype=np.float32)
out1 = model(test1)[0].numpy()
print(f"全0输入 → {out1}")

# 测试2: 全0.5输入（接近实际数据）
test2 = np.full((1, 30, 26), 0.5, dtype=np.float32)
out2 = model(test2)[0].numpy()
print(f"全0.5输入 → {out2}")

# 测试3: 随机输入
np.random.seed(42)
test3 = np.random.rand(1, 30, 26).astype(np.float32)
out3 = model(test3)[0].numpy()
print(f"随机输入 → {out3}")

# 测试4: 使用实际特征范围
test4 = np.random.uniform(0.4, 0.7, (1, 30, 26)).astype(np.float32)
out4 = model(test4)[0].numpy()
print(f"实际范围输入 (0.4-0.7) → {out4}")

print("\n========== 诊断结果 ==========")
# 检查是否总是输出 Neutral
neutral_outputs = [out1[2], out2[2], out3[2], out4[2]]
if all(n > 0.99 for n in neutral_outputs):
    print("❌ 错误：模型总是输出 Neutral (>0.99)")
    print("   可能原因：")
    print("   1. 模型未训练")
    print("   2. 模型权重全为0或常数")
    print("   3. 模型转换错误")
    print("\n   建议：检查原始模型文件或重新训练")
elif all(abs(out1[i] - out2[i]) < 0.01 for i in range(4)):
    print("⚠️  警告：不同输入产生相同输出")
    print("   模型可能退化为常数函数")
else:
    print("✅ 模型输出随输入变化，基本正常")
    print(f"   输出范围: Backhand [{min(o[0] for o in [out1,out2,out3,out4]):.4f}, {max(o[0] for o in [out1,out2,out3,out4]):.4f}]")
    print(f"   输出范围: Forehand [{min(o[1] for o in [out1,out2,out3,out4]):.4f}, {max(o[1] for o in [out1,out2,out3,out4]):.4f}]")
    print(f"   输出范围: Neutral  [{min(o[2] for o in [out1,out2,out3,out4]):.4f}, {max(o[2] for o in [out1,out2,out3,out4]):.4f}]")
    print(f"   输出范围: Serve    [{min(o[3] for o in [out1,out2,out3,out4]):.4f}, {max(o[3] for o in [out1,out2,out3,out4]):.4f}]")