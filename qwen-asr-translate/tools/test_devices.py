import pyaudio

p = pyaudio.PyAudio()
print("=== Audio Input Devices ===")
for i in range(p.get_device_count()):
    try:
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"{i}: {info['name']}")
            print(f"   Max Input Channels: {info['maxInputChannels']}")
            print(f"   Default Sample Rate: {info['defaultSampleRate']}")
            print()
    except Exception as e:
        print(f"Device {i}: Error - {e}")

p.terminate()
