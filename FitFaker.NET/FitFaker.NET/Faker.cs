using Dynastream.Fit;

namespace FitFaker.NET;

public static class Faker
{
    public static bool Fake(string fitFilePath)
    {
        FileStream? fileStream = null;
        try
        {
            fileStream = new FileStream(fitFilePath, FileMode.Open, FileAccess.ReadWrite);
            Console.WriteLine($"Opening {fileStream.Name}");

            var decoder = new Decode();
            var fitListener = new FitListener();
            decoder.MesgEvent += fitListener.OnMesg;
            if (!decoder.IsFIT(fileStream))
            {
                Console.WriteLine($"{fileStream.Name} is not a valid FIT file.");
                return false;
            }

            if (!decoder.Read(fileStream))
            {
                Console.WriteLine($"There was a problem decoding {fileStream.Name}.");
                return false;
            }

            foreach (var fileId in fitListener.FitMessages.FileIdMesgs)
            {
                fileId.SetManufacturer(Manufacturer.Garmin);
                fileId.SetProductName("");
                fileId.SetProduct(GarminProduct.Edge530Apac);
                fileId.SetGarminProduct(GarminProduct.Edge530Apac);
            }
            foreach (var deviceInfo in fitListener.FitMessages.DeviceInfoMesgs)
            {
                deviceInfo.SetManufacturer(Manufacturer.Garmin);
                deviceInfo.SetProductName("");
                deviceInfo.SetProduct(GarminProduct.Edge530Apac);
                deviceInfo.SetGarminProduct(GarminProduct.Edge530Apac);
                deviceInfo.SetSoftwareVersion(9.8f);
            }

            fileStream.Position = 0;
            fileStream.SetLength(0); // Clear the file before writing new data
            var encoder = new Encode(ProtocolVersion.V20);
            encoder.Open(fileStream);
            WriteMesgs(encoder, fitListener.FitMessages);

            encoder.Close();
            Console.WriteLine($"Successfully wrote to {fileStream.Name}");

            return true;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Exception: {ex.Message}");
            return false;
        }
        finally
        {
            if (fileStream != null)
            {
                fileStream.Close();
                fileStream.Dispose();
            }
        }
    }

    private static void WriteMesgs(Encode encoder, FitMessages messages)
    {
        // FileId (must be first)
        encoder.Write(messages.FileIdMesgs);

        // Required Mesgs
        encoder.Write(messages.SessionMesgs);
        encoder.Write(messages.LapMesgs);
        encoder.Write(messages.RecordMesgs);

        // Optional Mesgs
        // encoder.Write(messages.FileCreatorMesgs);

        var fileCreator = new FileCreatorMesg();
        fileCreator.SetSoftwareVersion(980);
        encoder.Write(fileCreator);

        encoder.Write(messages.TimestampCorrelationMesgs);
        encoder.Write(messages.SoftwareMesgs);
        encoder.Write(messages.SlaveDeviceMesgs);
        encoder.Write(messages.CapabilitiesMesgs);
        encoder.Write(messages.FileCapabilitiesMesgs);
        encoder.Write(messages.MesgCapabilitiesMesgs);
        encoder.Write(messages.FieldCapabilitiesMesgs);
        encoder.Write(messages.DeviceSettingsMesgs);
        encoder.Write(messages.UserProfileMesgs);
        encoder.Write(messages.HrmProfileMesgs);
        encoder.Write(messages.SdmProfileMesgs);
        encoder.Write(messages.BikeProfileMesgs);
        encoder.Write(messages.ConnectivityMesgs);
        encoder.Write(messages.WatchfaceSettingsMesgs);
        encoder.Write(messages.OhrSettingsMesgs);
        encoder.Write(messages.TimeInZoneMesgs);
        encoder.Write(messages.ZonesTargetMesgs);
        encoder.Write(messages.SportMesgs);
        encoder.Write(messages.HrZoneMesgs);
        encoder.Write(messages.SpeedZoneMesgs);
        encoder.Write(messages.CadenceZoneMesgs);
        encoder.Write(messages.PowerZoneMesgs);
        encoder.Write(messages.MetZoneMesgs);
        encoder.Write(messages.TrainingSettingsMesgs);
        encoder.Write(messages.DiveSettingsMesgs);
        encoder.Write(messages.DiveAlarmMesgs);
        encoder.Write(messages.DiveApneaAlarmMesgs);
        encoder.Write(messages.DiveGasMesgs);
        encoder.Write(messages.GoalMesgs);
        encoder.Write(messages.LengthMesgs);
        encoder.Write(messages.EventMesgs);
        encoder.Write(messages.DeviceInfoMesgs);
        encoder.Write(messages.DeviceAuxBatteryInfoMesgs);
        encoder.Write(messages.TrainingFileMesgs);
        encoder.Write(messages.WeatherConditionsMesgs);
        encoder.Write(messages.WeatherAlertMesgs);
        encoder.Write(messages.GpsMetadataMesgs);
        encoder.Write(messages.CameraEventMesgs);
        encoder.Write(messages.GyroscopeDataMesgs);
        encoder.Write(messages.AccelerometerDataMesgs);
        encoder.Write(messages.MagnetometerDataMesgs);
        encoder.Write(messages.BarometerDataMesgs);
        encoder.Write(messages.ThreeDSensorCalibrationMesgs);
        encoder.Write(messages.OneDSensorCalibrationMesgs);
        encoder.Write(messages.VideoFrameMesgs);
        encoder.Write(messages.ObdiiDataMesgs);
        encoder.Write(messages.NmeaSentenceMesgs);
        encoder.Write(messages.AviationAttitudeMesgs);
        encoder.Write(messages.VideoMesgs);
        encoder.Write(messages.VideoTitleMesgs);
        encoder.Write(messages.VideoDescriptionMesgs);
        encoder.Write(messages.VideoClipMesgs);
        encoder.Write(messages.SetMesgs);
        encoder.Write(messages.JumpMesgs);
        encoder.Write(messages.SplitMesgs);
        encoder.Write(messages.SplitSummaryMesgs);
        encoder.Write(messages.ClimbProMesgs);
        encoder.Write(messages.FieldDescriptionMesgs);
        encoder.Write(messages.DeveloperDataIdMesgs);
        encoder.Write(messages.CourseMesgs);
        encoder.Write(messages.CoursePointMesgs);
        encoder.Write(messages.SegmentIdMesgs);
        encoder.Write(messages.SegmentLeaderboardEntryMesgs);
        encoder.Write(messages.SegmentPointMesgs);
        encoder.Write(messages.SegmentLapMesgs);
        encoder.Write(messages.SegmentFileMesgs);
        encoder.Write(messages.WorkoutMesgs);
        encoder.Write(messages.WorkoutSessionMesgs);
        encoder.Write(messages.WorkoutStepMesgs);
        encoder.Write(messages.ExerciseTitleMesgs);
        encoder.Write(messages.ScheduleMesgs);
        encoder.Write(messages.TotalsMesgs);
        encoder.Write(messages.WeightScaleMesgs);
        encoder.Write(messages.BloodPressureMesgs);
        encoder.Write(messages.MonitoringInfoMesgs);
        encoder.Write(messages.MonitoringMesgs);
        encoder.Write(messages.MonitoringHrDataMesgs);
        encoder.Write(messages.Spo2DataMesgs);
        encoder.Write(messages.HrMesgs);
        encoder.Write(messages.StressLevelMesgs);
        encoder.Write(messages.MaxMetDataMesgs);
        encoder.Write(messages.HsaBodyBatteryDataMesgs);
        encoder.Write(messages.HsaEventMesgs);
        encoder.Write(messages.HsaAccelerometerDataMesgs);
        encoder.Write(messages.HsaGyroscopeDataMesgs);
        encoder.Write(messages.HsaStepDataMesgs);
        encoder.Write(messages.HsaSpo2DataMesgs);
        encoder.Write(messages.HsaStressDataMesgs);
        encoder.Write(messages.HsaRespirationDataMesgs);
        encoder.Write(messages.HsaHeartRateDataMesgs);
        encoder.Write(messages.HsaConfigurationDataMesgs);
        encoder.Write(messages.HsaWristTemperatureDataMesgs);
        encoder.Write(messages.MemoGlobMesgs);
        encoder.Write(messages.SleepLevelMesgs);
        encoder.Write(messages.AntChannelIdMesgs);
        encoder.Write(messages.AntRxMesgs);
        encoder.Write(messages.AntTxMesgs);
        encoder.Write(messages.ExdScreenConfigurationMesgs);
        encoder.Write(messages.ExdDataFieldConfigurationMesgs);
        encoder.Write(messages.ExdDataConceptConfigurationMesgs);
        encoder.Write(messages.DiveSummaryMesgs);
        encoder.Write(messages.AadAccelFeaturesMesgs);
        encoder.Write(messages.HrvMesgs);
        encoder.Write(messages.BeatIntervalsMesgs);
        encoder.Write(messages.HrvStatusSummaryMesgs);
        encoder.Write(messages.HrvValueMesgs);
        encoder.Write(messages.RawBbiMesgs);
        encoder.Write(messages.RespirationRateMesgs);
        encoder.Write(messages.ChronoShotSessionMesgs);
        encoder.Write(messages.ChronoShotDataMesgs);
        encoder.Write(messages.TankUpdateMesgs);
        encoder.Write(messages.TankSummaryMesgs);
        encoder.Write(messages.SleepAssessmentMesgs);
        encoder.Write(messages.SkinTempOvernightMesgs);
        encoder.Write(messages.PadMesgs);

        // Activity (must be last)
        encoder.Write(messages.ActivityMesgs);
    }
}
