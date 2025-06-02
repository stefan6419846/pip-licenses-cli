from boolean import Expression

class ExpressionInfo:
    errors: list[str]

class Licensing:
    def validate(self, expression: str) -> ExpressionInfo: ...
    def parse(self, expression: str) -> Expression | None: ...

def get_spdx_licensing() -> Licensing: ...
