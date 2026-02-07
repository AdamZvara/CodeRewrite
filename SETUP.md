# Setup Instructions

## 1. Fork EasyEdit

First, fork the EasyEdit repository to your GitHub account:

1. Go to https://github.com/zjunlp/EasyEdit
2. Click "Fork" to create your own copy
3. Note your fork URL: `https://github.com/YOUR_USERNAME/EasyEdit`

## 2. Add EasyEdit as Submodule

After forking, add your fork as a submodule:

```bash
cd knowledge-editing-code

# Add your fork as submodule
git submodule add https://github.com/YOUR_USERNAME/EasyEdit.git EasyEdit

# Also add upstream for syncing
cd EasyEdit
git remote add upstream https://github.com/zjunlp/EasyEdit.git
cd ..

# Commit the submodule
git add .gitmodules EasyEdit
git commit -m "Add EasyEdit fork as submodule"
```

## 3. (Optional) Add Diversity Datasets Submodule

If you need the diversity evaluation datasets:

```bash
git submodule add ../diversity-datasets diversity-datasets
git commit -m "Add diversity-datasets submodule"
```

## 4. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install main dependencies
pip install -r requirements.txt

# Install EasyEdit dependencies
pip install -r EasyEdit/requirements.txt
```

## 5. Syncing EasyEdit with Upstream

To get updates from the original EasyEdit repository:

```bash
cd EasyEdit
git fetch upstream
git merge upstream/main
# Resolve any conflicts with your custom changes
git push origin main
cd ..
git add EasyEdit
git commit -m "Update EasyEdit submodule"
```

## 6. Making Custom Changes to EasyEdit

When you need to add custom hyperparameters or modifications:

```bash
cd EasyEdit
# Make your changes
git add .
git commit -m "Add custom hyperparameters for code editing"
git push origin main
cd ..
git add EasyEdit
git commit -m "Update EasyEdit with custom changes"
```
