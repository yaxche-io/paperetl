"""
Sample module
"""

import re

import numpy as np

from text2digits.text2digits import Text2Digits

from .vocab import Vocab

class Sample(object):
    """
    Methods to extract the sample size of a study.
    """

    @staticmethod
    def extract(sections, attributes):
        """
        Attempts to extract sample size, sample and sample method using an attributes
        prediction model.

        Args:
            sections: list of sections
            attributes: attribute predictions for each section

        Returns:
            (size, sample, method)
        """

        size, sample, method = None, None, None

        # Get best attribute match per category
        best = np.argmax(attributes, axis=0)

        # labels - NO_MATCH, STATISTIC, SAMPLE_METHOD, SAMPLE_SIZE
        # section - name, text, tokens
        # Require minimum level of confidence for best prediction
        if best[2] >= 0.3:
            method = sections[best[2]][1]
        if best[3] >= 0.3:
            sample = sections[best[3]]

            # Attempt to extract size from sample size tokens
            # section - name, text, tokens
            size = Sample.find(sample[2], Vocab.SAMPLE)
            sample = sample[1]

        return size, sample, method

    @staticmethod
    def find(tokens, keywords):
        """
        Attempts to find a token that matches keywords having a numeric descriptor.
        i.e. 34 subjects, 30 patients, ten studies

        Args:
            token: NLP token
            keywords: list of keywords to match

        Returns:
            True if token matches keywords
        """

        matches = [Sample.match(token, keywords) for token in tokens]
        matches = [match for match in matches if match]

        return matches[0] if matches else None

    @staticmethod
    def match(token, keywords):
        """
        Compares a token against a list of keywords looking for a matching token with a
        numeric descriptor.

        Args:
            token: NLP token
            keywords: list of keywords to match

        Returns:
            list of matches if found or None
        """

        if token.text.lower() in keywords:
            matches = []

            # Get all numeric sequential children and join into single number
            for c in token.children:
                if Sample.isnumber(c):
                    matches.append(Sample.tonumber(c))
                elif matches:
                    break

            if matches:
                return "".join(matches)

        return None

    @staticmethod
    def isnumber(token):
        """
        Determines if token represents a number.

        Args:
            token: input token

        Returns:
            True if this represents a number, False otherwise
        """

        # Returns true if following conditions are met:
        #  - Token POS is a number of it's all digits
        #  - Token DEP is in [amod, nummod]
        #  - None of the children are brackets (ignore citations [1], [2], etc)
        return (token.text.isdigit() or token.pos_ == "NUM") and token.dep_ in ["amod", "nummod"] and not any([c.text == "[" for c in token.children])

    @staticmethod
    def tonumber(token):
        """
        Attempts to convert a string to a number. Returns raw token if unsuccessful.

        Args:
            token: input token

        Returns:
            parsed token
        """

        # Get text as root text with preceding (left) numeric prefixes
        text = token.text
        for c in reversed(list(token.lefts)):
            if c.text.isdigit() or c.pos_ == "NUM":
                text = "%s %s" % (c.text, text)
            else:
                break

        # Format text for numeric parsing
        text = text.replace(",", "")
        text = re.sub(r"(\d+)\s+(\d+)", r"\1\2", text)

        try:
            # Convert numeric words to numbers
            return text if text.isnumeric() else Text2Digits().convert(text)
        # pylint: disable=W0702
        except:
            pass

        return text
