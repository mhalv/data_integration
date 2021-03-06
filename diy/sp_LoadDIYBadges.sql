USE [DIY]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER PROCEDURE [dbo].[sp_LoadDIYBadges] AS 
BEGIN

		--0. ensure temp table doesn't exist in use
		IF OBJECT_ID(N'tempdb..#diy_badges') IS NOT NULL
		BEGIN
						DROP TABLE #diy_badges
		END
	
	--1. bulk load csv and SELECT INTO temp table
		SELECT sub.*
		INTO #diy_badges
		FROM
					(SELECT * 
					FROM OPENROWSET(
							'MSDASQL'
						,'Driver={Microsoft Access Text Driver (*.txt, *.csv)};DefaultDir=c:\data_robot\diy\data;'
						,'select * from c:\data_robot\diy\data\badges.csv')
					) sub;

		--2. upsert
		WITH new_badges AS (SELECT
     badge
    ,date_earned
    ,earned
    ,nickname
		FROM #diy_badges)

		MERGE diy_badges target
		USING new_badges staging
					ON target.badge = staging.badge
				AND target.nickname = staging.nickname
		WHEN MATCHED THEN
				UPDATE SET  
						target.date_earned = staging.date_earned
		WHEN NOT MATCHED BY target THEN
		INSERT (badge
									,nickname
         ,earned
									,date_earned) 
		VALUES (staging.badge
									,staging.nickname
         ,staging.earned
									,staging.date_earned);
END
				