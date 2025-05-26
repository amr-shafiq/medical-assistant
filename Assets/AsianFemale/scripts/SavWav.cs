using System;
using System.IO;
using UnityEngine;

public static class SavWav
{
    public static bool Save(string filepath, AudioClip clip)
    {
        if (clip == null)
        {
            Debug.LogError("AudioClip is null. Cannot save WAV file.");
            return false;
        }

        var filepathWithExtension = filepath.EndsWith(".wav") ? filepath : filepath + ".wav";

        try
        {
            using (var fileStream = CreateEmpty(filepathWithExtension))
            {
                ConvertAndWrite(fileStream, clip);
                WriteHeader(fileStream, clip);
            }

            if (File.Exists(filepathWithExtension))
            {
                Debug.Log($"WAV file saved successfully to {filepathWithExtension}");
                return true;
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"Error saving WAV file: {ex.Message}");
        }

        return false;
    }

    static FileStream CreateEmpty(string filepath)
    {
        var fileStream = new FileStream(filepath, FileMode.Create);
        for (int i = 0; i < 44; i++) // Space for WAV header
            fileStream.WriteByte(0);
        return fileStream;
    }

    static void ConvertAndWrite(FileStream fileStream, AudioClip clip)
    {
        float[] samples = new float[clip.samples * clip.channels];
        clip.GetData(samples, 0);

        short[] intData = new short[samples.Length];
        byte[] bytesData = new byte[samples.Length * 2];

        const int rescaleFactor = 32767; // To convert float to short

        for (int i = 0; i < samples.Length; i++)
        {
            // Ensure samples are within the valid range
            float clampedSample = Mathf.Clamp(samples[i], -1f, 1f);
            intData[i] = (short)(clampedSample * rescaleFactor);
            byte[] byteArr = BitConverter.GetBytes(intData[i]);
            byteArr.CopyTo(bytesData, i * 2);
        }

        fileStream.Write(bytesData, 0, bytesData.Length);
    }

    static void WriteHeader(FileStream fileStream, AudioClip clip)
    {
        fileStream.Seek(0, SeekOrigin.Begin);

        int sampleRate = clip.frequency;
        int channels = clip.channels;
        int samples = clip.samples;

        var header = new byte[44];
        Buffer.BlockCopy(new char[4] { 'R', 'I', 'F', 'F' }, 0, header, 0, 4);
        Buffer.BlockCopy(BitConverter.GetBytes(fileStream.Length - 8), 0, header, 4, 4);
        Buffer.BlockCopy(new char[4] { 'W', 'A', 'V', 'E' }, 0, header, 8, 4);
        Buffer.BlockCopy(new char[4] { 'f', 'm', 't', ' ' }, 0, header, 12, 4);
        Buffer.BlockCopy(BitConverter.GetBytes(16), 0, header, 16, 4); // Subchunk1 size
        Buffer.BlockCopy(BitConverter.GetBytes((short)1), 0, header, 20, 2); // Audio format (PCM)
        Buffer.BlockCopy(BitConverter.GetBytes((short)channels), 0, header, 22, 2);
        Buffer.BlockCopy(BitConverter.GetBytes(sampleRate), 0, header, 24, 4);
        Buffer.BlockCopy(BitConverter.GetBytes(sampleRate * channels * 2), 0, header, 28, 4); // Byte rate
        Buffer.BlockCopy(BitConverter.GetBytes((short)(channels * 2)), 0, header, 32, 2); // Block align
        Buffer.BlockCopy(BitConverter.GetBytes((short)16), 0, header, 34, 2); // Bits per sample
        Buffer.BlockCopy(new char[4] { 'd', 'a', 't', 'a' }, 0, header, 36, 4);
        Buffer.BlockCopy(BitConverter.GetBytes(samples * channels * 2), 0, header, 40, 4);

        fileStream.Write(header, 0, header.Length);
    }
}


