import subprocess
import matplotlib.pyplot as plt
import re

# Set the range and step size for sched_min_granularity_ns and sched_wakeup_granularity_ns values
start_value = 1000000
end_value = 30000000
step_size = 500000

# Generate the sched_min_granularity_ns and sched_wakeup_granularity_ns values
sched_min_granularity_ns_values = list(range(start_value, end_value + 1, step_size))
sched_wakeup_granularity_ns_values = list(range(start_value, end_value + 1, step_size))

perf_g = 20  # processors option for perf-bench
perf_l = 1000  # loops option for perf-bench

runtime_min_granularity = []
avg_delays_min_granularity = []
max_delays_min_granularity = []
runtime_wakeup_granularity = []
avg_delays_wakeup_granularity = []
max_delays_wakeup_granularity = []

def set_parameter(parameter, value):
    try:
        echo_command = f'echo {value} > /sys/kernel/debug/sched/{parameter}'
        subprocess.run(echo_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error setting parameter: {e}")

def run_perf_bench(g, l):
    # Perform latency recording
    subprocess.run(['sudo', 'perf', 'record', '-e', 'sched:*', 'perf', 'bench', 'sched', 'messaging', '-p', '-t', '-g', str(g), '-l', str(l)], text=True)

    # Run perf sched latency command and capture the output
    output = subprocess.check_output(['sudo', 'perf', 'sched', 'latency'], text=True)
    lines = output.strip().split('\n')

    # Find the line that contains the sched-messaging task information
    stress_line = None
    for line in lines:
        if line.startswith('  sched-messaging:'):
            stress_line = line
            break

    # Extract the delay data from the stress line
    if stress_line is not None:
        stress_data = stress_line.split('|')
        runtime = float(stress_data[1].strip().split('ms')[0].strip())

        avg_delay_match = re.search(r'avg:\s*([\d.]+)\s*ms', stress_data[3])
        avg_delay = float(avg_delay_match.group(1))

        max_delay_match = re.search(r'max:\s*([\d.]+)\s*ms', stress_data[4])
        max_delay = float(max_delay_match.group(1))

        return runtime, avg_delay, max_delay
    else:
        print('sched-messaging data not found in the output')
        return None, None, None

def Plotting(num, x, y, xlabel, ylabel, title):
    plt.figure(num)
    plt.plot(x, y)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.savefig(f'result/{title}.png')

for value in sched_min_granularity_ns_values:
    set_parameter('min_granularity_ns', value)
    runtime, avg_delay, max_delay = run_perf_bench(perf_g, perf_l)
    if avg_delay is not None and max_delay is not None:
        runtime_min_granularity.append(runtime)
        avg_delays_min_granularity.append(avg_delay)
        max_delays_min_granularity.append(max_delay)
        print(f'min_granularity_ns: {value}, runtime: {runtime}, Avg Delay: {avg_delay}, Max Delay: {max_delay}')
    else:
        print(f"Delay data not available for sched_min_granularity_ns={value}")

# Reset the parameters to default values
set_parameter('min_granularity_ns', 3000000)

for value in sched_wakeup_granularity_ns_values:
    set_parameter('wakeup_granularity_ns', value)
    runtime, avg_delay, max_delay = run_perf_bench(perf_g, perf_l)
    if avg_delay is not None and max_delay is not None:
        runtime_wakeup_granularity.append(runtime)
        avg_delays_wakeup_granularity.append(avg_delay)
        max_delays_wakeup_granularity.append(max_delay)
        print(f'wakeup_granularity_ns: {value}, runtime: {runtime}, Avg Delay: {avg_delay}, Max Delay: {max_delay}')
    else:
        print(f"Delay data not available for sched_min_granularity_ns={value}")

# Reset the parameters to default values
set_parameter('wakeup_granularity_ns', 4000000)

# Plotting for sched_min_granularity_ns
Plotting(0, sched_min_granularity_ns_values, runtime_min_granularity, 'sched_min_granularity_ns', 'time (ms)', 'sched_min_granularity_ns_time')
Plotting(1, sched_min_granularity_ns_values, avg_delays_min_granularity, 'sched_min_granularity_ns', 'Average Delay(ms)', 'sched_min_granularity_ns_AVG_Delay')
Plotting(2, sched_min_granularity_ns_values, max_delays_min_granularity, 'sched_min_granularity_ns','Max Delay(ms)' , 'sched_min_granularity_ns_Max_Delay')
Plotting(3, sched_wakeup_granularity_ns_values, runtime_wakeup_granularity, 'wakeup_granularity_ns', 'time (ms)', 'wakeup_granularity_ns_time')
Plotting(4, sched_wakeup_granularity_ns_values, avg_delays_wakeup_granularity, 'wakeup_granularity_ns', 'Average Delay(ms)', 'wakeup_granularity_ns_AVG_Delay')
Plotting(5, sched_wakeup_granularity_ns_values, max_delays_wakeup_granularity, 'wakeup_granularity_ns','Max Delay(ms)' , 'wakeup_granularity_ns_Max_Delay')