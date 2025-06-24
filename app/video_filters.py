import subprocess

def invert_colors(input, output):
    command = [
        "ffmpeg", "-y", "-i", input,
        "-vf", "lutyuv=y=negval:u=negval:v=negval",
        output
    ]
    try:
        subprocess.run(command, check=True)
        print(f"Inverted video saved to {output}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        raise

def grayscale_filter(input, output):
    command = [
        "ffmpeg", "-y", "-i", input,
        "-vf", "format=gray",
        output
    ]
    try:
        subprocess.run(command, check=True)
        print(f"Grayscale video saved to {output}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        raise
