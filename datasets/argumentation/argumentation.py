# coding=utf-8
# Copyright 2020 HuggingFace Datasets Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""Introduction to the CoNLL-2003 Shared Task: Language-Independent Named Entity Recognition"""

import os

import datasets


logger = datasets.logging.get_logger(__name__)

_TRAINING_FILE = "train_mining.tsv"
_DEV_FILE = "dev_mining.tsv"
_TEST_FILE = "test_mining.tsv"


class ArgumentationConfig(datasets.BuilderConfig):
    """BuilderConfig for Argumentation"""

    def __init__(self, **kwargs):
        """BuilderConfig forArgumentation.
        Args:
          **kwargs: keyword arguments forwarded to super.
        """
        super(ArgumentationConfig, self).__init__(**kwargs)


class Argumentation(datasets.GeneratorBasedBuilder):
    """Argumentation dataset."""

    BUILDER_CONFIGS = [
        ArgumentationConfig(name="argumentation", version=datasets.Version("1.0.0"), description="Argumentation dataset"),
    ]

    def _info(self):
        return datasets.DatasetInfo(
            features=datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "tokens": datasets.Sequence(datasets.Value("string")),
                    "ner_tags": datasets.Sequence(
                        datasets.features.ClassLabel(
                            names=[
                                "O",
                                "B-Claim",
                                "I-Claim",
                                "B-Premise",
                                "I-Premise",
                            ]
                        )
                    ),
                }
            ),
            supervised_keys=None,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        data_files = {
            "train": os.path.join(os.getcwd(), _TRAINING_FILE),
            "dev": os.path.join(os.getcwd(), _DEV_FILE),
            "test": os.path.join(os.getcwd(), _TEST_FILE),
        }

        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"filepath": data_files["train"]}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={"filepath": data_files["dev"]}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={"filepath": data_files["test"]}),
        ]

    def _generate_examples(self, filepath):
        logger.info("⏳ Generating examples from = %s", filepath)
        with open(filepath, encoding="utf-8") as f:
            guid = 0
            tokens = []
            ner_tags = []
            for line in f:
                if line.startswith("-DOCSTART-") or line == "" or line == "\n":
                    if tokens:
                        yield guid, {
                            "id": str(guid),
                            "tokens": tokens,
                            "ner_tags": ner_tags,
                        }
                        guid += 1
                        tokens = []
                        ner_tags = []
                else:
                    splits = line.split("\t")
                    tokens.append(splits[0])
                    ner_tags.append(splits[1].rstrip())
            # last example
            yield guid, {
                "id": str(guid),
                "tokens": tokens,
                "ner_tags": ner_tags,
            }