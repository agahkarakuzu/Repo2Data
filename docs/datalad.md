# Datalad Provider

The Datalad provider enables you to work with git-annex repositories and datasets managed by [DataLad](https://www.datalad.org/).

## What is DataLad?

DataLad is a free and open-source distributed data management system that keeps track of your data, creates structure, ensures reproducibility, supports collaboration, and integrates with existing infrastructures. It's built on top of git-annex and is widely used in neuroscience and other research fields.

## Installation

### Install Repo2Data

```bash
pip install repo2data
```

### Install DataLad

DataLad must be installed separately:

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install datalad
```

**macOS:**
```bash
brew install datalad
```

**Using conda:**
```bash
conda install -c conda-forge datalad
```

**Using pip:**
```bash
pip install datalad
```

For detailed installation instructions, visit: [https://www.datalad.org/get_datalad.html](https://www.datalad.org/get_datalad.html)

## How It Works

The Datalad provider:

1. **Detects git repository URLs** ending with `.git`
2. **Uses `datalad install`** to clone and set up the repository
3. **Downloads the dataset** to your specified destination
4. **Preserves git-annex structure** for version control and data management

## Configuration

### Basic Configuration

```yaml
data:
  src: "https://github.com/OpenNeuroDatasets/ds000001.git"
  dst: "./data"
  projectName: "ds000001"
```

### Required Fields

- **`src`**: Git repository URL (must end with `.git`)
- **`dst`**: Destination directory where dataset will be installed
- **`projectName`**: Name for the dataset (used for caching and organization)

### Optional Fields

- **`version`**: Git reference (tag, branch, commit) for reproducibility

## URL Format

The Datalad provider recognizes URLs ending with `.git`:

```
https://github.com/OpenNeuroDatasets/ds000001.git
git@github.com:user/dataset.git
https://gin.g-node.org/organization/dataset.git
```

## Examples

### Example 1: OpenNeuro Dataset

Download a brain imaging dataset from OpenNeuro:

```yaml
data:
  src: "https://github.com/OpenNeuroDatasets/ds000001.git"
  dst: "./data"
  projectName: "openneuro_ds000001"
  version: "v1.0.0"
```

**Use in Python:**

```python
from repo2data import Repo2Data
from repo2data.utils import locate_evidence_data

# Download the dataset
r2d = Repo2Data("myst.yml")
r2d.install()

# Locate and use the data
data_path = locate_evidence_data("openneuro_ds000001")
print(f"Dataset location: {data_path}")

# Access dataset files
participants_file = data_path / "participants.tsv"
```

### Example 2: Custom DataLad Repository

```yaml
data:
  src: "https://gin.g-node.org/my_lab/experiment_2024.git"
  dst: "./data"
  projectName: "lab_experiment_2024"
```

**Download from command line:**

```bash
repo2data myst.yml
```

### Example 3: Multiple DataLad Datasets

Download several datasets in one configuration:

```yaml
data:
  dataset1:
    src: "https://github.com/OpenNeuroDatasets/ds000001.git"
    dst: "./data"
    projectName: "ds000001"
    version: "1.0.0"

  dataset2:
    src: "https://github.com/OpenNeuroDatasets/ds000002.git"
    dst: "./data"
    projectName: "ds000002"
    version: "1.0.0"
```

### Example 4: Using from Jupyter Notebook

```python
# In your notebook at: repo/content/analysis/preprocessing.ipynb
from repo2data.utils import locate_evidence_data
import nibabel as nib
import os

# Locate the dataset (works from any directory depth)
data_path = locate_evidence_data("openneuro_ds000001")

# Access specific subject data
subject_dir = data_path / "sub-01"
anat_file = subject_dir / "anat" / "sub-01_T1w.nii.gz"

# Load neuroimaging data
img = nib.load(str(anat_file))
print(f"Image shape: {img.shape}")
```

## Working with DataLad Datasets

### Get Specific Files

After installing with Repo2Data, you can use DataLad commands to get specific files:

```bash
cd data/openneuro_ds000001
datalad get sub-01/anat/*
```

### Check Dataset Status

```bash
cd data/openneuro_ds000001
datalad status
```

### Update Dataset

```bash
cd data/openneuro_ds000001
datalad update --merge
```

## Common Use Cases

### Neuroscience Research (OpenNeuro)

OpenNeuro hosts many public brain imaging datasets as DataLad repositories:

```yaml
data:
  src: "https://github.com/OpenNeuroDatasets/ds003097.git"
  dst: "./data"
  projectName: "naturalistic_viewing_study"
  version: "1.0.3"
```

Browse datasets at: [https://openneuro.org](https://openneuro.org)

### Lab Data Management

Use DataLad for version-controlled research data:

```yaml
data:
  src: "git@github.com:mylab/private-dataset.git"
  dst: "./data"
  projectName: "lab_private_data"
```

### Collaborative Projects

Share datasets with collaborators using git-annex:

```yaml
data:
  src: "https://gin.g-node.org/collaboration/shared-dataset.git"
  dst: "./data"
  projectName: "collaborative_dataset"
```

## Advantages of DataLad Provider

1. **Version Control**: Full git history of dataset changes
2. **Efficient Storage**: git-annex handles large files efficiently
3. **Partial Downloads**: Get only the files you need
4. **Provenance Tracking**: Complete record of data transformations
5. **Reproducibility**: Pin specific versions with git tags/commits

## Troubleshooting

### DataLad Not Installed

**Error**: `FileNotFoundError: datalad is not installed`

**Solution**: Install DataLad following the [installation guide](https://www.datalad.org/get_datalad.html)

### SSH Authentication Required

**Error**: Git asks for SSH key password during clone

**Solution**: Set up SSH keys for the git host:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add key to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Add public key to GitHub/GitLab/GIN settings
cat ~/.ssh/id_ed25519.pub
```

### Dataset Already Exists

**Error**: `datalad install failed` because directory exists

**Solution**:
- Delete existing directory: `rm -rf data/projectName`
- Or use cache: Repo2Data will skip re-download if cache is valid

### Permission Denied

**Error**: Cannot access private repository

**Solution**:
- Ensure you have access rights to the repository
- Use SSH URL instead of HTTPS for private repos
- Configure git credentials: `git config --global credential.helper store`

## Best Practices

1. **Use version tags** for reproducibility:
   ```yaml
   version: "v1.0.3"
   ```

2. **Pin specific commits** for exact reproducibility:
   ```yaml
   version: "a3f8d9c2"
   ```

3. **Document dataset source**: Include OpenNeuro ID or repository details in your README

4. **Get files as needed**: Don't download entire dataset if you only need specific files

5. **Cache intelligently**: Repo2Data caches DataLad installations - version changes trigger re-download

## Integration with DataLad Features

After installing with Repo2Data, you can use all DataLad features:

```bash
# Get specific files
datalad get data/openneuro_ds000001/sub-*/anat/*

# Run analysis with provenance tracking
datalad run -m "Preprocessing" python preprocess.py

# Save results
datalad save -m "Analysis results"

# Check dataset integrity
datalad fsck
```

## Related Resources

- [DataLad Documentation](https://docs.datalad.org/)
- [DataLad Handbook](http://handbook.datalad.org/)
- [OpenNeuro Datasets](https://openneuro.org)
- [GIN (G-Node Infrastructure)](https://gin.g-node.org)

## Back to Main Guide

Return to the [main documentation](./data.md) for general Repo2Data features and other providers.
