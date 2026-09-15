"""Always-on world process. Deployment milestone: durable heartbeat until the real calendar scheduler is attached."""
import time
from . import world
def main():
 world.update(state="RUNNING",message="APEXGRID world worker online")
 while True:
  time.sleep(5);world.update(message="APEXGRID world is alive")
if __name__=='__main__':main()
