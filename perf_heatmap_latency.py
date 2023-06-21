import subprocess
import matplotlib.pyplot as plt
import numpy as np
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

total_times = np.zeros((len(sched_min_granularity_ns_values), len(sched_wakeup_granularity_ns_values)))
avg_delays = np.zeros((len(sched_min_granularity_ns_values), len(sched_wakeup_granularity_ns_values)))
max_delays = np.zeros((len(sched_min_granularity_ns_values), len(sched_wakeup_granularity_ns_values)))

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

def plot_heatmap(data, x_values, y_values, label, xlabel, ylabel, filename):
    plt.figure()
    plt.imshow(data, cmap='gray', origin='lower', extent=[min(x_values), max(x_values), min(y_values), max(y_values)])
    plt.colorbar(label=label)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title('min_granularity to wakeup_granularity heatmap')
    plt.savefig(filename)
    # plt.show()

for i, min_granularity_ns in enumerate(sched_min_granularity_ns_values):
    for j, wakeup_granularity_ns in enumerate(sched_wakeup_granularity_ns_values):
        set_parameter('min_granularity_ns', min_granularity_ns)
        set_parameter('wakeup_granularity_ns', wakeup_granularity_ns)
        runtime, avg_delay, max_delay = run_perf_bench(perf_g, perf_l)
        if avg_delay is not None and max_delay is not None:
            total_times[i, j] = runtime
            avg_delays[i, j] = avg_delay
            max_delays[i, j] = max_delay
            print(f'min_granularity_ns: {min_granularity_ns}, wakeup_granularity_ns: {wakeup_granularity_ns}, runtime: {runtime}, Avg Delay: {avg_delay}, Max Delay: {max_delay}')
        else:
            print(f"Delay data not available for sched_min_granularity_ns={min_granularity_ns}, wakeup_granularity_ns={wakeup_granularity_ns}")

# Reset the parameters to default values
set_parameter('min_granularity_ns', 3000000)
set_parameter('wakeup_granularity_ns', 4000000)

# Plotting heatmaps
plot_heatmap(total_times, sched_wakeup_granularity_ns_values, sched_min_granularity_ns_values, 'time(ms)', 'sched_wakeup_granularity_ns', 'sched_min_granularity_ns', 'result/total_time_heatmap.png')
plot_heatmap(avg_delays, sched_wakeup_granularity_ns_values, sched_min_granularity_ns_values, 'Avg Delay(ms)', 'sched_wakeup_granularity_ns', 'sched_min_granularity_ns', 'result/avg_delay_heatmap.png')
plot_heatmap(max_delays, sched_wakeup_granularity_ns_values, sched_min_granularity_ns_values, 'Max Delay(ms)', 'sched_wakeup_granularity_ns', 'sched_min_granularity_ns', 'result/max_delay_heatmap.png')
