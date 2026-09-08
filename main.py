from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback

app = FastAPI(title="Maya Mock API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MayaNode:
    def __init__(self, name, node_type):
        self.name = name
        self.node_type = node_type
        self.attrs = {}

class MayaMockEnvironment:
    def __init__(self):
        self.nodes = {"persp": MayaNode("persp", "camera")}
        self.selection = []

    def spaceLocator(self, **kwargs):
        name = kwargs.get("name", f"locator#{len(self.nodes)}")
        if name in self.nodes:
            raise RuntimeError(f"# Error: A object with name '{name}' already exists.")
        self.nodes[name] = MayaNode(name, "locator")
        self.selection = [name]
        return [name]

    def select(self, target=None, **kwargs):
        if kwargs.get("clear", False):
            self.selection = []
            return
        if not target:
            return self.selection
        targets = [target] if isinstance(target, str) else target
        for t in targets:
            if t not in self.nodes:
                raise RuntimeError(f"# Error: No object matches name: {t}")
        self.selection = targets

    def ls(self, *args, **kwargs):
        if kwargs.get("selection", False):
            return list(self.selection)
        return list(self.nodes.keys())

cmds = MayaMockEnvironment()

class CodeRequest(BaseModel):
    code: str

@app.post("/execute")
async def execute_code(req: CodeRequest):
    local_env = {"cmds": cmds}
    global_env = {}
    
    try:
        exec(req.code, global_env, local_env)
        return {
            "status": "success",
            "output": "Executed successfully.",
            "scene_nodes": list(cmds.nodes.keys()),
            "selection": cmds.selection
        }
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        error_line = "Unknown"
        for frame in reversed(tb):
            if frame.filename == "<string>":
                error_line = frame.lineno
                break
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
            "line": error_line,
            "traceback": traceback.format_exc()
        }
