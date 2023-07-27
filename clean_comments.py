import ast
import argparse

def remove_comments_and_docstrings(source):
    """
    Given Python source code, remove the comments and docstrings.
    """
    class RemoveCommentsAndDocstrings(ast.NodeTransformer):
        """
        This class uses the NodeTransformer methods to traverse the AST 
        and remove nodes that correspond to comments or docstrings.
        """
        def visit_Expr(self, node):
            if isinstance(node.value, ast.Str):  # for docstrings
                return None
            return node

    tree = ast.parse(source)
    tree = RemoveCommentsAndDocstrings().visit(tree)
    return ast.unparse(tree)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Remove comments and docstrings from Python source code.')
    parser.add_argument('sourcefile', type=str, help='The Python source file to clean up.')
    parser.add_argument('outputfile', type=str, help='The cleaned Python source file output.')
    
    args = parser.parse_args()
    
    with open(args.sourcefile, 'r') as f:
        source = f.read()
    
    cleaned_source = remove_comments_and_docstrings(source)
    
    with open(args.outputfile, 'w') as f:
        f.write(cleaned_source)