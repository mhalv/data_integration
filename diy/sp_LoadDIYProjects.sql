USE [DIY]
GO
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER PROCEDURE [dbo].[sp_LoadDIYProjects] AS 
BEGIN

		--0. ensure temp table doesn't exist in use
		IF OBJECT_ID(N'tempdb..#diy_projects') IS NOT NULL
		BEGIN
						DROP TABLE #diy_projects
		END
	
	--1. bulk load csv and SELECT INTO temp table
		SELECT sub.*
		INTO #diy_projects
		FROM
					(SELECT * 
					FROM OPENROWSET(
							'MSDASQL'
						,'Driver={Microsoft Access Text Driver (*.txt, *.csv)};DefaultDir=c:\data_robot\diy\data;'
						,'select * from c:\data_robot\diy\data\projects.csv')
					) sub;

		--2. upsert
		WITH new_projects AS 
				(SELECT *
				 FROM #diy_projects)

		MERGE diy_projects target
		USING new_projects staging
					ON target.url = staging.url
		WHEN MATCHED THEN
				UPDATE SET  
						target.title = staging.title
					,target.comments = staging.comments
     ,target.created = staging.created
					,target.featured = staging.featured
					,target.favorites = staging.favorites
     ,target.forks = staging.forks
					,target.skill = staging.skill
					,target.nickname = staging.nickname
		WHEN NOT MATCHED BY target THEN
		INSERT (title
									,url
									,comments
         ,created
									,featured
									,favorites
         ,forks
									,skill
									,nickname) 
		VALUES (staging.title
									,staging.url
									,staging.comments
         ,staging.created
									,staging.featured
									,staging.favorites
         ,staging.forks
									,staging.skill
									,staging.nickname);
END
				
