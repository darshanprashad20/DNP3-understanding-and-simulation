from pydnp3 import opendnp3, openpal, asiopal, asiodnp3
import time

# Sleep duration for asynchronous operations
SLEEP_SECONDS = 5

# Create the DNP3 Manager
log_handler = asiodnp3.ConsoleLogger().Create()
manager = asiodnp3.DNP3Manager(1, log_handler)

# Setup TCP channel to connect to the slave simulator
retry = asiopal.ChannelRetry().Default()
listener = asiodnp3.PrintingChannelListener().Create()
channel = manager.AddTCPClient(
    'client',
    opendnp3.levels.NORMAL,
    retry,
    '127.0.0.1',
    '0.0.0.0',
    20000,
    listener
)


# Sequence of Events Handler for receiving values
class SOEHandler(opendnp3.ISOEHandler):
    def __init__(self):
        super().__init__()

    def Process(self, info, values):
        print("Received data:")
        values.Foreach(lambda value: print(f"Index: {value.index}, Value: {value.value.value}"))

    def Start(self):
        pass

    def End(self):
        pass


soe_handler = SOEHandler()

# Configure the master stack
master_application = asiodnp3.DefaultMasterApplication().Create()
stack_config = asiodnp3.MasterStackConfig()
stack_config.master.responseTimeout = openpal.TimeDuration().Seconds(5)
stack_config.link.RemoteAddr = 1  # Ensure this matches your slave configuration

# Create and enable the master
master = channel.AddMaster(
    'master',
    soe_handler,
    master_application,
    stack_config
)
master.Enable()

# Give the channel time to establish the connection
time.sleep(SLEEP_SECONDS)

# Scan Class 1 data to fetch both Binary and Analog outputs
print('Reading initial values...')
master.ScanClasses(opendnp3.ClassField(opendnp3.ClassField.CLASS_1))
time.sleep(SLEEP_SECONDS)

# Send a control command to toggle the binary output
print('Toggling Binary Output to ON...')
command_callback = asiodnp3.PrintingCommandCallback.Get()
command_set = opendnp3.CommandSet([
    opendnp3.WithIndex(opendnp3.ControlRelayOutputBlock(opendnp3.ControlCode.LATCH_ON), 0)
])
master.DirectOperate(command_set, command_callback)
time.sleep(SLEEP_SECONDS)

# Fetch values again after toggling
print('Reading values after control operation...')
master.ScanClasses(opendnp3.ClassField(opendnp3.ClassField.CLASS_1))
time.sleep(SLEEP_SECONDS)

# Properly shutdown the master and channel
master.Disable()
master = None
channel.Shutdown()
channel = None
manager.Shutdown()
