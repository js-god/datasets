# coding=utf-8
# Copyright 2018 The TensorFlow Datasets Authors.
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

"""IMDB movie reviews dataset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import tensorflow as tf
from tensorflow_datasets.core import api_utils
import tensorflow_datasets.public_api as tfds

_DESCRIPTION = """\
Large Movie Review Dataset.
This is a dataset for binary sentiment classification containing substantially \
more data than previous benchmark datasets. We provide a set of 25,000 highly \
polar movie reviews for training, and 25,000 for testing.\
"""

_CITATION = """\
@InProceedings{maas-EtAl:2011:ACL-HLT2011,
  author    = {Maas, Andrew L.  and  Daly, Raymond E.  and  Pham, Peter T.  and  Huang, Dan  and  Ng, Andrew Y.  and  Potts, Christopher},
  title     = {Learning Word Vectors for Sentiment Analysis},
  booktitle = {Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics: Human Language Technologies},
  month     = {June},
  year      = {2011},
  address   = {Portland, Oregon, USA},
  publisher = {Association for Computational Linguistics},
  pages     = {142--150},
  url       = {http://www.aclweb.org/anthology/P11-1015}
}
"""

_DOWNLOAD_URL = "http://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"


class IMDBReviewsConfig(tfds.core.BuilderConfig):
  """BuilderConfig for IMDBReviews."""

  @api_utils.disallow_positional_args
  def __init__(self, text_encoder_config=None, **kwargs):
    """BuilderConfig for IMDBReviews.

    Args:
      text_encoder_config: `tfds.features.text.TextEncoderConfig`, configuration
        for the `tfds.features.text.TextEncoder` used for the IMDB `"text"`
        feature.
      **kwargs: keyword arguments forwarded to super.
    """
    super(IMDBReviewsConfig, self).__init__(**kwargs)
    self.text_encoder_config = (
        text_encoder_config or tfds.features.text.TextEncoderConfig())


class IMDBReviews(tfds.core.GeneratorBasedBuilder):
  """IMDB movie reviews dataset."""
  BUILDER_CONFIGS = [
      IMDBReviewsConfig(
          name="plain_text",
          version="0.0.1",
          description="Plain text",
      ),
      IMDBReviewsConfig(
          name="bytes",
          version="0.0.1",
          description=("Uses byte-level text encoding with "
                       "`tfds.features.text.ByteTextEncoder`"),
          text_encoder_config=tfds.features.text.TextEncoderConfig(
              encoder=tfds.features.text.ByteTextEncoder()),
      ),
      IMDBReviewsConfig(
          name="subwords8k",
          version="0.0.1",
          description=("Uses `tfds.features.text.SubwordTextEncoder` with 8k "
                       "vocab size"),
          text_encoder_config=tfds.features.text.TextEncoderConfig(
              encoder_cls=tfds.features.text.SubwordTextEncoder,
              vocab_size=2**13),
      ),
      IMDBReviewsConfig(
          name="subwords32k",
          version="0.0.1",
          description=("Uses `tfds.features.text.SubwordTextEncoder` with "
                       "32k vocab size"),
          text_encoder_config=tfds.features.text.TextEncoderConfig(
              encoder_cls=tfds.features.text.SubwordTextEncoder,
              vocab_size=2**15),
      ),
  ]

  def _info(self):
    return tfds.core.DatasetInfo(
        name=self.name,
        description=_DESCRIPTION,
        version=self._builder_config.version,
        config_name=self._builder_config.name,
        features=tfds.features.FeaturesDict({
            "text": tfds.features.Text(
                encoder_config=self._builder_config.text_encoder_config),
            "label": tfds.features.ClassLabel(names=["neg", "pos"]),
        }),
        supervised_keys=("text", "label"),
        urls=["http://ai.stanford.edu/~amaas/data/sentiment/"],
        size_in_bytes=85 * tfds.units.MiB,
        citation=_CITATION,
    )

  def _vocab_text_gen(self, train_dir):
    for ex in self._generate_examples(train_dir):
      yield ex["text"]

  def _split_generators(self, dl_manager):
    imdb_path = dl_manager.download_and_extract(_DOWNLOAD_URL)

    train_dir = os.path.join(imdb_path, "aclImdb", "train")
    test_dir = os.path.join(imdb_path, "aclImdb", "test")

    # Generate vocabulary from training data if SubwordTextEncoder configured
    self.info.features["text"].maybe_build_from_corpus(
        self._vocab_text_gen(train_dir))

    return [
        tfds.core.SplitGenerator(
            name=tfds.Split.TRAIN,
            num_shards=10,
            gen_kwargs={"directory": train_dir}),
        tfds.core.SplitGenerator(
            name=tfds.Split.TEST,
            num_shards=10,
            gen_kwargs={"directory": test_dir}),
    ]

  def _generate_examples(self, directory):
    """Generate IMDB examples."""
    pos_dir = os.path.join(directory, "pos")
    neg_dir = os.path.join(directory, "neg")

    for d, label in [(pos_dir, "pos"), (neg_dir, "neg")]:
      for filename in tf.gfile.ListDirectory(d):
        with tf.gfile.Open(os.path.join(d, filename)) as imdb_f:
          text = imdb_f.read().strip()
          yield self.info.features.encode_example({
              "text": text,
              "label": label,
          })
