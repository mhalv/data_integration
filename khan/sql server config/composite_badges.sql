USE [Khan]
GO

/****** Object:  Table [dbo].[composite_badges]    Script Date: 02/07/2014 19:10:31 ******/
IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[composite_badges]') AND type in (N'U'))
DROP TABLE [dbo].[composite_badges]
GO

USE [Khan]
GO

/****** Object:  Table [dbo].[composite_badges]    Script Date: 02/07/2014 19:10:36 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

SET ANSI_PADDING ON
GO

CREATE TABLE [dbo].[composite_badges](
	[count] [int] NULL,
	[owned] [char](5) NULL,
	[slug] [varchar](255) NULL,
	[student] [varchar](255) NULL
) ON [PRIMARY]

GO

SET ANSI_PADDING OFF
GO


