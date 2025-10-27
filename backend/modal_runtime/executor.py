import modal
import json
from typing import Dict, Any

# Import the Modal app and image from app.py
from .app import app, image

class SandboxExecutor:
    """Manages per-session Modal Sandboxes with persistent state."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        
        # Create per-session volume for persistent workspace
        self.volume = modal.Volume.from_name(
            f"lg-urban-session-{session_id}", 
            create_if_missing=True
        )
        
        # Create sandbox with volume mounted
        self.sandbox = modal.Sandbox.create(
            app=app,
            image=image,
            timeout=60*60*2,  # 2 hours session timeout
            idle_timeout=60*10,  # 10 min idle timeout
            volumes={"/workspace": self.volume},
            workdir="/workspace"
        )
        
        # Start driver program with stdin/stdout pipes
        # PIPE allows bidirectional communication with the driver
        self.process = self.sandbox.exec(
            "python", "/root/driver.py",
            stdin=modal.PIPE,   # Send commands to driver
            stdout=modal.PIPE   # Receive responses from driver
        )
    
    def execute(self, code: str, timeout: int = 120) -> Dict[str, Any]:
        """Execute code and return results.
        
        The driver handles all artifact scanning and S3 upload,
        so we just need to send the code and return the response.
        """
        try:
            # Send command to driver
            command = json.dumps({"code": code})
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            
            # Read response line
            result_line = self.process.stdout.readline()
            result = json.loads(result_line)
            
            # Driver already handled artifacts, just return result
            return result
            
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Execution failed: {str(e)}",
                "artifacts": []
            }
    
    def terminate(self):
        """Clean up sandbox and persist volume."""
        try:
            # Close stdin to signal driver to exit
            self.process.stdin.close()
            
            # Wait for process to finish gracefully
            self.process.wait(timeout=30)
            
        except Exception as e:
            print(f"Error during graceful termination: {e}")
            
        finally:
            # Always terminate sandbox
            self.sandbox.terminate()
            self.sandbox.wait(raise_on_termination=False)
            
            # Volume will persist automatically for future sessions
