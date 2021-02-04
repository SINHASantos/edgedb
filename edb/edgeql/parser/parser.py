#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2008-present MagicStack Inc. and the EdgeDB authors.
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
#

from __future__ import annotations

from edb import errors
from edb.common import debug, parsing

from .grammar import rust_lexer, tokens, keywords
from .grammar import expressions as gr_exprs


class EdgeQLParserBase(parsing.Parser):
    def get_debug(self):
        return debug.flags.edgeql_parser

    def get_exception(self, native_err, context, token=None):
        msg = native_err.args[0]

        if isinstance(native_err, errors.EdgeQLSyntaxError):
            return native_err
        else:
            if msg.startswith('Unexpected token: '):
                token = token or getattr(native_err, 'token', None)
                ltok = self.parser._stack[-1][0]

                if not token or token.kind() == 'EOF':
                    msg = 'Unexpected end of line'
                elif (
                    token.kind() == 'IDENT' and
                    isinstance(ltok, parsing.Nonterm)
                ):
                    # Make sure that the previous element in the stack
                    # is some kind of Nonterminal, because if it's
                    # not, this is probably not an issue of a missing
                    # COMMA.

                    msg = f'Unexpected {token.text()!r}'
                    # There are a few things this could be, so we make
                    # an attempt to distinguish some specific parsing
                    # error in shapes.

                    # Then check if LBRACE, LPAREN, or LBRACKET is in
                    # the parser stack. Any one of those indicates
                    # that the parser was in the middle of processing
                    # a list of some sort (shape, tuple, or array) and
                    # encountering an unexpected IDENT probably
                    # indicates a missing COMMA instead.
                    for i, (el, _) in enumerate(reversed(self.parser._stack)):
                        if isinstance(el, tokens.Token):
                            if isinstance(el, tokens.T_LBRACE):
                                if (
                                    isinstance(ltok, gr_exprs.Identifier) and
                                    ltok.val in keywords.edgeql_keywords
                                ):
                                    # This is some [unreserved]
                                    # keyword preceding the unexpected
                                    # IDENT in a shape, which probably
                                    # is not a case of a missing COMMA
                                    # anymore.
                                    break
                                else:
                                    msg = (f"Missing ',' before the shape "
                                           f"item {token.text()!r}")

                                break
                            elif isinstance(el, tokens.T_LPAREN):
                                msg = (f"Missing ',' before the tuple "
                                       f"item {token.text()!r}")
                                break
                            elif isinstance(el, tokens.T_LBRACKET):
                                # This is either an array literal or
                                # array index.
                                prevt = self.parser._stack[-2 - i][0]
                                if isinstance(prevt, gr_exprs.Expr):
                                    msg = \
                                        "Missing ':' in array slice expression"
                                else:
                                    msg = (f"Missing ',' before the array "
                                           f"item {token.text()!r}")
                                break

                elif hasattr(token, 'val'):
                    msg = f'Unexpected {token.val!r}'
                elif token.kind() == 'NL':
                    msg = 'Unexpected end of line'
                else:
                    msg = f'Unexpected {token.text()!r}'

        return errors.EdgeQLSyntaxError(msg, context=context, token=token)

    def get_lexer(self):
        return rust_lexer.EdgeQLLexer()


class EdgeQLExpressionParser(EdgeQLParserBase):
    def get_parser_spec_module(self):
        from .grammar import single
        return single


class EdgeQLBlockParser(EdgeQLParserBase):
    def get_parser_spec_module(self):
        from .grammar import block
        return block


class EdgeSDLParser(EdgeQLParserBase):
    def get_parser_spec_module(self):
        from .grammar import sdldocument
        return sdldocument
