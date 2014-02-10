USE [Khan]
GO

/****** Object:  Table [dbo].[composite_exercises]    Script Date: 02/07/2014 18:31:22 ******/
IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[composite_exercises]') AND type in (N'U'))
DROP TABLE [dbo].[composite_exercises]
GO

USE [Khan]
GO

/****** Object:  Table [dbo].[composite_exercises]    Script Date: 02/07/2014 18:31:22 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

SET ANSI_PADDING ON
GO

CREATE TABLE [dbo].[composite_exercises](
	[streak] [int] NULL,
	[total_done] [int] NULL,
	[practiced] [char](5) NULL,
	[level] [varchar](20) NULL,
	[last_done] [datetime] NULL,
	[proficient] [char](5) NULL,
	[maximum_exercise_progress_dt] [datetime] NULL,
	[mastered] [char](5) NULL,
	[student] [varchar](255) NULL,
	[longest_streak] [int] NULL,
	[progress] [float] NULL,
	[practiced_date] [datetime] NULL,
	[total_corrrect] [int] NULL,
	[struggling] [char](5) NULL,
	[exercise] [varchar](255) NULL,
	[proficient_date] [datetime] NULL
) ON [PRIMARY]

GO

SET ANSI_PADDING OFF
GO


