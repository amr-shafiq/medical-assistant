using System;

public class WAV
{
    public float[] LeftChannel { get; private set; }
    public float[] RightChannel { get; private set; }
    public int ChannelCount { get; private set; }
    public int SampleCount { get; private set; }
    public int Frequency { get; private set; }

    // Constructor that parses a WAV file from byte data
    public WAV(byte[] wavFile)
    {
        // Parse the header
        ChannelCount = BitConverter.ToInt16(wavFile, 22);
        Frequency = BitConverter.ToInt32(wavFile, 24);
        int dataChunkOffset = FindDataChunkOffset(wavFile);
        int dataSize = BitConverter.ToInt32(wavFile, dataChunkOffset + 4);

        SampleCount = dataSize / 2 / ChannelCount;

        LeftChannel = new float[SampleCount];
        if (ChannelCount == 2)
            RightChannel = new float[SampleCount];

        // Convert data to float
        int dataStart = dataChunkOffset + 8;
        int index = 0;
        for (int i = 0; i < SampleCount; i++)
        {
            LeftChannel[i] = BitConverter.ToInt16(wavFile, dataStart + index) / 32768f;
            index += 2;

            if (ChannelCount == 2)
            {
                RightChannel[i] = BitConverter.ToInt16(wavFile, dataStart + index) / 32768f;
                index += 2;
            }
        }
    }

    private int FindDataChunkOffset(byte[] wavFile)
    {
        for (int i = 12; i < wavFile.Length - 8; i++)
        {
            if (wavFile[i] == 'd' && wavFile[i + 1] == 'a' && wavFile[i + 2] == 't' && wavFile[i + 3] == 'a')
                return i;
        }
        throw new Exception("Data chunk not found in WAV file.");
    }
}

