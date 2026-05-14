# ============================================================
# EV RouteIQ — EfficientNet-B4 Training Script (Upload to Kaggle)
# Dataset: RSCD 1-Million (cristvollerei/rscd-dataset-1million)
# Train: 300K | Val: 27K | Test: 27K | Classes: 27 | Epochs: 70
# ============================================================

import subprocess
subprocess.run(["pip", "install", "timm", "kagglehub", "-q"], check=True)

import os, shutil, random, time, json
from pathlib import Path
from tqdm import tqdm
import torch, torch.nn as nn, torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import timm, numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (classification_report, confusion_matrix,
                              accuracy_score, f1_score)

print(f"PyTorch {torch.__version__} | CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# ── Download Dataset ─────────────────────────────────────────
import kagglehub
dataset_path = kagglehub.dataset_download("cristvollerei/rscd-dataset-1million")
print(f"Dataset: {dataset_path}")

def find_folder(base, keywords):
    for root, dirs, _ in os.walk(base):
        for d in dirs:
            if any(k in d.lower() for k in keywords):
                return os.path.join(root, d)
    return None

train_src = find_folder(dataset_path, ["train"])
val_src   = find_folder(dataset_path, ["val", "vali"])
test_src  = find_folder(dataset_path, ["test"])

# ── Create Properly Structured Subsets ───────────────────────
# CRITICAL FIX: val/test get class subfolders (not flat class_0)
WORK_DIR = "/kaggle/working"
SUBSET_TRAIN = f"{WORK_DIR}/subset_train"
SUBSET_VAL   = f"{WORK_DIR}/subset_val"
SUBSET_TEST  = f"{WORK_DIR}/subset_test"

CLASS_KEYWORDS_MAP = {
    'dry_asphalt_severe': ['dry-asphalt-severe'],
    'dry_asphalt_slight': ['dry-asphalt-slight'],
    'dry_asphalt_smooth': ['dry-asphalt-smooth'],
    'dry_concrete_severe': ['dry-concrete-severe'],
    'dry_concrete_slight': ['dry-concrete-slight'],
    'dry_concrete_smooth': ['dry-concrete-smooth'],
    'dry_gravel': ['dry-gravel'],
    'dry_mud': ['dry-mud'],
    'fresh_snow': ['fresh_snow', 'fresh-snow'],
    'ice': ['-ice.jpg'],
    'melted_snow': ['melted_snow', 'melted-snow'],
    'water_asphalt_severe': ['water-asphalt-severe'],
    'water_asphalt_slight': ['water-asphalt-slight'],
    'water_asphalt_smooth': ['water-asphalt-smooth'],
    'water_concrete_severe': ['water-concrete-severe'],
    'water_concrete_slight': ['water-concrete-slight'],
    'water_concrete_smooth': ['water-concrete-smooth'],
    'water_gravel': ['water-gravel'],
    'water_mud': ['water-mud'],
    'wet_asphalt_severe': ['wet-asphalt-severe'],
    'wet_asphalt_slight': ['wet-asphalt-slight'],
    'wet_asphalt_smooth': ['wet-asphalt-smooth'],
    'wet_concrete_severe': ['wet-concrete-severe'],
    'wet_concrete_slight': ['wet-concrete-slight'],
    'wet_concrete_smooth': ['wet-concrete-smooth'],
    'wet_gravel': ['wet-gravel'],
    'wet_mud': ['wet-mud'],
}

def create_subset_from_class_folders(source_dir, dest_dir, n_per_class, seed=42):
    """For train (already has class folders)."""
    random.seed(seed)
    os.makedirs(dest_dir, exist_ok=True)
    classes = [d for d in os.listdir(source_dir)
               if os.path.isdir(os.path.join(source_dir, d))]
    total = 0
    for cls in tqdm(classes, desc=Path(dest_dir).name, ncols=90):
        src_c = os.path.join(source_dir, cls)
        dst_c = os.path.join(dest_dir, cls)
        os.makedirs(dst_c, exist_ok=True)
        imgs = [f for f in os.listdir(src_c)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        n = min(n_per_class, len(imgs))
        for f in random.sample(imgs, n):
            shutil.copy2(os.path.join(src_c, f), os.path.join(dst_c, f))
        total += n
    print(f"  {Path(dest_dir).name}: {total:,} images")
    return total

def create_subset_from_flat(source_dir, dest_dir, n_per_class, seed=42):
    """For val/test (flat folders) — sort by filename keyword."""
    random.seed(seed)
    os.makedirs(dest_dir, exist_ok=True)
    all_imgs = [f for f in os.listdir(source_dir)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    buckets = {cls: [] for cls in CLASS_KEYWORDS_MAP}
    for img in all_imgs:
        img_lower = img.lower()
        for cls, keywords in CLASS_KEYWORDS_MAP.items():
            if any(kw in img_lower for kw in keywords):
                buckets[cls].append(img)
                break
    total = 0
    for cls, imgs in tqdm(buckets.items(), desc=Path(dest_dir).name, ncols=90):
        dst_c = os.path.join(dest_dir, cls)
        os.makedirs(dst_c, exist_ok=True)
        n = min(n_per_class, len(imgs))
        if n == 0:
            print(f"  WARNING: 0 images for {cls}")
            continue
        for f in random.sample(imgs, n):
            shutil.copy2(os.path.join(source_dir, f), os.path.join(dst_c, f))
        total += n
    print(f"  {Path(dest_dir).name}: {total:,} images")
    return total

print("\nCreating subsets (this may take ~15 min)...")
create_subset_from_class_folders(train_src, SUBSET_TRAIN, 11111)
create_subset_from_flat(val_src,   SUBSET_VAL,   1000)
create_subset_from_flat(test_src,  SUBSET_TEST,  1000)

# ── Transforms ───────────────────────────────────────────────
IMG_SIZE = 380

train_tfm = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.1),
    transforms.RandomRotation(degrees=15),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.1),
    transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.2, scale=(0.02, 0.15)),
])
val_tfm = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

train_ds = datasets.ImageFolder(SUBSET_TRAIN, transform=train_tfm)
val_ds   = datasets.ImageFolder(SUBSET_VAL,   transform=val_tfm)
test_ds  = datasets.ImageFolder(SUBSET_TEST,  transform=val_tfm)

CLASS_NAMES = train_ds.classes
NUM_CLASSES = len(CLASS_NAMES)
print(f"\nClasses ({NUM_CLASSES}): {CLASS_NAMES}")

train_loader = DataLoader(train_ds, batch_size=32, shuffle=True,
                          num_workers=4, pin_memory=True)
val_loader   = DataLoader(val_ds,   batch_size=64, shuffle=False,
                          num_workers=4, pin_memory=True)
test_loader  = DataLoader(test_ds,  batch_size=64, shuffle=False,
                          num_workers=4, pin_memory=True)

# ── EfficientNet-B4 Model ────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class EVRouteIQModel(nn.Module):
    def __init__(self, num_classes=27):
        super().__init__()
        self.backbone = timm.create_model(
            'efficientnet_b4', pretrained=True, num_classes=0, global_pool='avg')
        in_f = self.backbone.num_features  # 1792
        self.head = nn.Sequential(
            nn.BatchNorm1d(in_f),
            nn.Dropout(0.4),
            nn.Linear(in_f, 512),
            nn.SiLU(),
            nn.BatchNorm1d(512),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
    def forward(self, x):
        return self.head(self.backbone(x))

model = EVRouteIQModel(NUM_CLASSES).to(device)
print(f"Params: {sum(p.numel() for p in model.parameters()):,}")

# ── Loss, Optimizer, Scheduler ───────────────────────────────
class LabelSmoothCE(nn.Module):
    def __init__(self, eps=0.1):
        super().__init__()
        self.eps = eps
    def forward(self, pred, target):
        n = pred.size(-1)
        log_p = nn.functional.log_softmax(pred, dim=-1)
        loss = -log_p.gather(-1, target.unsqueeze(1)).squeeze(1)
        smooth = -log_p.mean(-1)
        return ((1 - self.eps) * loss + self.eps * smooth).mean()

criterion = LabelSmoothCE(eps=0.1)
optimizer = optim.AdamW([
    {'params': model.backbone.parameters(), 'lr': 3e-4},
    {'params': model.head.parameters(),     'lr': 1e-3},
], weight_decay=1e-4)

EPOCHS = 70
scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
    optimizer, T_0=10, T_mult=2, eta_min=1e-6)
scaler = GradScaler()

# ── Training Loop ────────────────────────────────────────────
SAVE_PATH    = f"{WORK_DIR}/best_model_ev_routeiq.pth"
PATIENCE     = 10
best_val_acc = 0.0
no_improve   = 0
history      = {'train_loss': [], 'train_acc': [],
                'val_loss': [],   'val_acc': [], 'lr': []}

print(f"\nTraining EfficientNet-B4 for {EPOCHS} epochs...")
print("=" * 80)

for epoch in range(1, EPOCHS + 1):
    t0 = time.time()
    # TRAIN
    model.train()
    tl, tc, tt = 0.0, 0, 0
    for imgs, labels in tqdm(train_loader, desc=f"Ep{epoch:02d} Train", ncols=90):
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        with autocast():
            out  = model(imgs)
            loss = criterion(out, labels)
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(optimizer); scaler.update()
        tl += loss.item() * imgs.size(0)
        tc += (out.argmax(1) == labels).sum().item()
        tt += labels.size(0)
    scheduler.step()
    train_loss, train_acc = tl / tt, tc / tt

    # VALIDATE
    model.eval()
    vl, vc, vt = 0.0, 0, 0
    with torch.no_grad():
        for imgs, labels in tqdm(val_loader, desc=f"Ep{epoch:02d} Val  ", ncols=90):
            imgs, labels = imgs.to(device), labels.to(device)
            with autocast():
                out  = model(imgs)
                loss = criterion(out, labels)
            vl += loss.item() * imgs.size(0)
            vc += (out.argmax(1) == labels).sum().item()
            vt += labels.size(0)
    val_loss, val_acc = vl / vt, vc / vt

    lr = optimizer.param_groups[0]['lr']
    history['train_loss'].append(train_loss); history['train_acc'].append(train_acc)
    history['val_loss'].append(val_loss);     history['val_acc'].append(val_acc)
    history['lr'].append(lr)

    print(f"\nEp{epoch:02d}/{EPOCHS} | TrainLoss:{train_loss:.4f} Acc:{train_acc:.4f} | "
          f"ValLoss:{val_loss:.4f} Acc:{val_acc:.4f} | LR:{lr:.2e} | {time.time()-t0:.0f}s")

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        no_improve   = 0
        torch.save({'epoch': epoch, 'state_dict': model.state_dict(),
                    'val_acc': val_acc, 'class_names': CLASS_NAMES,
                    'img_size': IMG_SIZE, 'num_classes': NUM_CLASSES},
                   SAVE_PATH)
        print(f"   BEST SAVED! Val Acc: {val_acc*100:.2f}%")
    else:
        no_improve += 1
        if no_improve >= PATIENCE:
            print(f"\nEarly stop at epoch {epoch}"); break

    with open(f"{WORK_DIR}/training_history.json", 'w') as f:
        json.dump(history, f)

print(f"\nTraining Done | Best Val Acc: {best_val_acc*100:.2f}%")

# ── Plot Curves ──────────────────────────────────────────────
ep = range(1, len(history['train_acc']) + 1)
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
axes[0].plot(ep, history['train_acc'], label='Train', color='#00D4FF', lw=2)
axes[0].plot(ep, history['val_acc'],   label='Val',   color='#39FF14', lw=2)
axes[0].set_title('Accuracy'); axes[0].legend(); axes[0].grid(alpha=0.3)
axes[1].plot(ep, history['train_loss'], color='#FF6B6B', lw=2, label='Train')
axes[1].plot(ep, history['val_loss'],   color='#FFD93D', lw=2, label='Val')
axes[1].set_title('Loss'); axes[1].legend(); axes[1].grid(alpha=0.3)
axes[2].plot(ep, history['lr'], color='#C77DFF', lw=2)
axes[2].set_title('Learning Rate'); axes[2].grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{WORK_DIR}/training_curves.png", dpi=150)
plt.show()

# ── Test Evaluation ──────────────────────────────────────────
ckpt = torch.load(SAVE_PATH, map_location=device)
model.load_state_dict(ckpt['state_dict'])
model.eval()
preds_all, labels_all = [], []
with torch.no_grad():
    for imgs, labels in tqdm(test_loader, desc="Test Eval", ncols=80):
        with autocast():
            out = model(imgs.to(device))
        preds_all.extend(out.argmax(1).cpu().numpy())
        labels_all.extend(labels.numpy())

test_acc = accuracy_score(labels_all, preds_all)
test_f1  = f1_score(labels_all, preds_all, average='weighted')
print(f"\nTEST ACCURACY: {test_acc*100:.2f}% | F1: {test_f1:.4f}")
print(classification_report(labels_all, preds_all, target_names=CLASS_NAMES))

# Confusion Matrix
cm = confusion_matrix(labels_all, preds_all, normalize='true')
plt.figure(figsize=(22, 20))
sns.heatmap(cm, annot=True, fmt='.2f', cmap='Blues',
            xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, annot_kws={"size": 7})
plt.title('EV RouteIQ — Confusion Matrix', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{WORK_DIR}/confusion_matrix.png", dpi=150)
plt.show()

# Save summary
summary = {"model": "EfficientNet-B4", "num_classes": NUM_CLASSES,
           "class_names": CLASS_NAMES, "best_val_acc": best_val_acc,
           "test_acc": test_acc, "test_f1": test_f1,
           "best_epoch": ckpt['epoch'], "img_size": IMG_SIZE}
with open(f"{WORK_DIR}/model_summary.json", 'w') as f:
    json.dump(summary, f, indent=2)
print(f"\nFiles saved: best_model_ev_routeiq.pth, training_history.json, model_summary.json")
print(f"DONE! Best Val Acc: {best_val_acc*100:.2f}%")
