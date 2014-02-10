USE [Khan]
GO

/****** Object:  Table [dbo].[stu_detail]    Script Date: 02/07/2014 19:55:00 ******/
IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[stu_detail]') AND type in (N'U'))
DROP TABLE [dbo].[stu_detail]
GO

USE [Khan]
GO

/****** Object:  Table [dbo].[stu_detail]    Script Date: 02/07/2014 19:55:01 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

SET ANSI_PADDING ON
GO

CREATE TABLE [dbo].[stu_detail](
	[badge_lev1] [int] NULL,
	[badge_lev0] [int] NULL,
	[badge_lev3] [int] NULL,
	[badge_lev2] [int] NULL,
	[badge_lev5] [int] NULL,
	[badge_lev4] [int] NULL,
	[first_visit] [datetime] NULL,
	[all_proficient_exercises] [varchar](MAX) NULL,
	[identity_email] [varchar](MAX) NULL,
	[registration_date] [datetime] NULL,
	[joined] [datetime] NULL,
	[username] [varchar](255) NULL,
	[coaches] [varchar](4000) NULL,
	[profile_root] [varchar](255) NULL,
	[points] [int] NULL,
	[student] [varchar](255) NULL,
	[proficient_exercises] [varchar](MAX) NULL,
	[total_seconds_watched] [int] NULL,
	[nickname] [varchar](255) NULL
) 

GO

SET ANSI_PADDING OFF
GO


