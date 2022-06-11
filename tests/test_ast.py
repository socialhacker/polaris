import unittest

import source.ast as ast

class TestAST(unittest.TestCase):

    def test_constant(self):
        self.assertEqual(ast.evaluate({}, ast.Constant(12)), 12)
        self.assertEqual(ast.evaluate({}, ast.Constant("test")), "test")

    def test_unary(self):
        self.assertEqual(ast.evaluate({}, ast.UnaryOp("-", ast.Constant(12))), -12)
        self.assertEqual(ast.evaluate({}, ast.UnaryOp("+", ast.Constant(11))),  11)

    def test_binary(self):
        self.assertEqual(
            ast.evaluate({}, ast.BinaryOp(ast.Constant(12), "+", ast.Constant(10))), 22)

        self.assertEqual(
            ast.evaluate({}, ast.BinaryOp(ast.Constant(10), "-", ast.Constant(12))), -2)

        self.assertAlmostEqual(
            ast.evaluate({}, ast.BinaryOp(ast.Constant(12), "*", ast.Constant(10))), 120)

        self.assertAlmostEqual(
            ast.evaluate({}, ast.BinaryOp(ast.Constant(12), "/", ast.Constant(10))), 1.2)

    def test_variable(self):
        self.assertEqual(ast.evaluate({"foo": 4}, ast.Variable("foo")), 4)

    def test_function(self):
        self.assertEqual(
            ast.evaluate({"v": 1},
                         ast.Function(lambda s, a: ast.evaluate(s, a),
                                      [ast.BinaryOp(ast.Variable("v"), "+", ast.Constant(7))])),
            8)

if __name__ == '__main__':
    unittest.main()
