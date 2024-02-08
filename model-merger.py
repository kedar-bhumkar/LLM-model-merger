# -*- coding: utf-8 -*-
"""Cloned LazyMergekit.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WY0l_4Itr4edzMGAk8mXpJBinfZCqMCB

# 🥱 LazyMergekit

> 🗣️ [Large Language Model Course](https://github.com/mlabonne/llm-course)

❤️ Created by [@maximelabonne](https://twitter.com/maximelabonne).

This notebook allows you to easily merge multiple models using [mergekit](https://github.com/cg123/mergekit). To evaluate your merges, see [🧐 LLM AutoEval](https://colab.research.google.com/drive/1Igs3WZuXAIv9X0vwqiE90QlEPys8e8Oa?usp=sharing#scrollTo=elyxjYI_rY5W).

*Special thanks to [@cg123](https://github.com/cg123) for this library and [@mrfakename](https://gist.github.com/fakerybakery) who told me about sharding (see his [Gist](https://gist.github.com/fakerybakery/d30a4d31b4f914757c1381166b9c683b)).*
"""

MODEL_NAME = "NeuralPipe-7B-slerp"
yaml_config = """
slices:
  - sources:
      - model: OpenPipe/mistral-ft-optimized-1218
        layer_range: [0, 32]
      - model: mlabonne/NeuralHermes-2.5-Mistral-7B
        layer_range: [0, 32]
merge_method: slerp
base_model: OpenPipe/mistral-ft-optimized-1218
parameters:
  t:
    - filter: self_attn
      value: [0, 0.5, 0.3, 0.7, 1]
    - filter: mlp
      value: [1, 0.5, 0.7, 0.3, 0]
    - value: 0.5
dtype: bfloat16
"""

# @title ## Run merge

# @markdown ### Runtime type
# @markdown Select your runtime (CPU, High RAM, GPU)

runtime = "CPU + High-RAM" # @param ["CPU", "CPU + High-RAM", "GPU"]

# @markdown ### Mergekit arguments
# @markdown Use the `main` branch by default, [`mixtral`](https://github.com/cg123/mergekit/blob/mixtral/moe.md) if you want to create a Mixture of Experts.

branch = "main" # @param ["main", "mixtral"]
trust_remote_code = False # @param {type:"boolean"}

# Install mergekit
if branch == "main":
    !git clone https://github.com/cg123/mergekit.git
    !cd mergekit && pip install -qqq -e . --progress-bar off
elif branch == "mixtral":
    !git clone -b mixtral https://github.com/cg123/mergekit.git
    !cd mergekit && pip install -qqq -e . --progress-bar off
    !pip install -qqq -U transformers --progress-bar off

# Save config as yaml file
with open('config.yaml', 'w', encoding="utf-8") as f:
    f.write(yaml_config)

# Base CLI
if branch == "main":
    cli = "mergekit-yaml config.yaml merge --copy-tokenizer"
elif branch == "mixtral":
    cli = "mergekit-moe config.yaml merge --copy-tokenizer"

# Additional arguments
if runtime == "CPU":
    cli += " --allow-crimes --out-shard-size 1B --lazy-unpickle"
elif runtime == "GPU":
    cli += " --cuda --low-cpu-memory"
if trust_remote_code:
    cli += " --trust-remote-code"

print(cli)

# Merge models
!{cli}

# @title ## Upload model to Hugging Face { display-mode: "form" }
# @markdown Enter your username the name of Colab secret that stores your [Hugging Face access token](https://huggingface.co/settings/tokens).
username = 'kedarbhumkar' # @param {type:"string"}
token = '' # @param {type:"string"}

!pip install -qU huggingface_hub

import yaml

from huggingface_hub import ModelCard, ModelCardData, HfApi
from google.colab import userdata
from jinja2 import Template

if branch == "main":
    template_text = """
---
license: apache-2.0
tags:
- merge
- mergekit
- lazymergekit
{%- for model in models %}
- {{ model }}
{%- endfor %}
---

# {{ model_name }}

{{ model_name }} is a merge of the following models using [LazyMergekit](https://colab.research.google.com/drive/1obulZ1ROXHjYLn6PPZJwRR6GzgQogxxb?usp=sharing):

{%- for model in models %}
* [{{ model }}](https://huggingface.co/{{ model }})
{%- endfor %}

## 🧩 Configuration

```yaml
{{- yaml_config -}}
```

## 💻 Usage

```python
!pip install -qU transformers accelerate

from transformers import AutoTokenizer
import transformers
import torch

model = "{{ username }}/{{ model_name }}"
messages = [{"role": "user", "content": "What is a large language model?"}]

tokenizer = AutoTokenizer.from_pretrained(model)
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
pipeline = transformers.pipeline(
    "text-generation",
    model=model,
    torch_dtype=torch.float16,
    device_map="auto",
)

outputs = pipeline(prompt, max_new_tokens=256, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
print(outputs[0]["generated_text"])
```
"""

    # Create a Jinja template object
    jinja_template = Template(template_text.strip())

    # Get list of models from config
    data = yaml.safe_load(yaml_config)
    if "models" in data:
        models = [data["models"][i]["model"] for i in range(len(data["models"])) if "parameters" in data["models"][i]]
    elif "parameters" in data:
        models = [data["slices"][0]["sources"][i]["model"] for i in range(len(data["slices"][0]["sources"]))]
    elif "slices" in data:
        models = [data["slices"][i]["sources"][0]["model"] for i in range(len(data["slices"]))]
    else:
        raise Exception("No models or slices found in yaml config")

    # Fill the template
    content = jinja_template.render(
        model_name=MODEL_NAME,
        models=models,
        yaml_config=yaml_config,
        username=username,
    )

elif branch == "mixtral":
    template_text = """
---
license: apache-2.0
tags:
- moe
- merge
- mergekit
- lazymergekit
{%- for model in models %}
- {{ model }}
{%- endfor %}
---

# {{ model_name }}

{{ model_name }} is a Mixure of Experts (MoE) made with the following models using [LazyMergekit](https://colab.research.google.com/drive/1obulZ1ROXHjYLn6PPZJwRR6GzgQogxxb?usp=sharing):

{%- for model in models %}
* [{{ model }}](https://huggingface.co/{{ model }})
{%- endfor %}

## 🧩 Configuration

```yaml
{{- yaml_config -}}
```

## 💻 Usage

```python
!pip install -qU transformers bitsandbytes accelerate

from transformers import AutoTokenizer
import transformers
import torch

model = "{{ username }}/{{ model_name }}"

tokenizer = AutoTokenizer.from_pretrained(model)
pipeline = transformers.pipeline(
    "text-generation",
    model=model,
    model_kwargs={"torch_dtype": torch.float16, "load_in_4bit": True},
)

messages = [{"role": "user", "content": "Explain what a Mixture of Experts is in less than 100 words."}]
prompt = pipeline.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
outputs = pipeline(prompt, max_new_tokens=256, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
print(outputs[0]["generated_text"])
```
"""

    # Create a Jinja template object
    jinja_template = Template(template_text.strip())

    # Fill the template
    data = yaml.safe_load(yaml_config)
    models = [model['source_model'] for model in data['experts']]

    content = jinja_template.render(
        model_name=MODEL_NAME,
        models=models,
        yaml_config=yaml_config,
        username=username,
    )

# Save the model card
card = ModelCard(content)
card.save('merge/README.md')

# Defined in the secrets tab in Google Colab
api = HfApi(token=userdata.get(token))

# Upload merge folder
api.create_repo(
    repo_id=f"{username}/{MODEL_NAME}",
    repo_type="model"
)
api.upload_folder(
    repo_id=f"{username}/{MODEL_NAME}",
    folder_path="merge",
)